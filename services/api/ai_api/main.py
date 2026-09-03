"""Apartment Intelligence v2 API (FastAPI). Closed schemas, session-bound studies, visible-click
confirmation challenge, one analysis at a time with a 15 s worker timeout, deterministic exports."""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import math
import json
import os
import secrets
import threading
import time
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from ai_geometry.build import Placement, build_scene, unit_frame
from ai_geometry.schema import PlateRecipe, UnitRecipe, canonical_json
from ai_geometry.writers import write_3dm, write_glb, write_obj
from ai_solar.result import run_analysis

from .cards import cards_bundle
from .store import CHALLENGE_TTL, Store, Study

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
WEB_DIST = Path(os.environ.get("AI_WEB_DIST", ROOT / "apps/web/dist"))
ANALYSIS_TIMEOUT_S = float(os.environ.get("AI_ANALYSIS_TIMEOUT_S", "15"))
MAX_BODY = 256 * 1024
MAX_EXPORT = 20 * 1024 * 1024
SESSION_COOKIE = "ai_session"
# Optional origin allow-list for state-changing requests, e.g. "https://apartments.senibina.com.sg". Empty = no check (local dev).
EXPECTED_ORIGINS = {o.strip().rstrip("/") for o in os.environ.get("AI_EXPECTED_ORIGINS", "").split(",") if o.strip()}
COOKIE_SECURE = os.environ.get("AI_COOKIE_SECURE", "false").lower() == "true"

PRECINCT = json.loads((DATA / "precinct/dawson-v2.json").read_text())
PLATE = PlateRecipe.model_validate(json.loads((DATA / "recipes/skyville-block87-plate.recipe.json").read_text()))
UNITS = {v: UnitRecipe.model_validate(json.loads((DATA / f"recipes/4r-type-{v.lower()}.recipe.json").read_text())) for v in "ABC"}
SUPPORTED = [{"address": PRECINCT["target"]["address"], "postal_code": PRECINCT["target"]["postal_code"], "block": PRECINCT["target"]["block"], "storey_range": PRECINCT["target"]["storey_range"], "demo_storey": PRECINCT["target"]["demo_storey"], "development": "SkyVille @ Dawson", "unit_types": ["4R"], "variants": ["A", "B", "C"], "facades": ["NE", "NW", "SW", "SE"], "stack_positions": ["end", "inner"]}]

store = Store()
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_analysis_lock = threading.Lock()
app = FastAPI(title="Apartment Intelligence v2", version="2.0.0", docs_url=None, redoc_url=None)


def err(status: int, code: str, next_action: str):
    return HTTPException(status_code=status, detail={"error": code, "next_action": next_action})


@app.exception_handler(HTTPException)
async def _http_exc(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": str(exc.detail), "next_action": "Check the request and try again."}
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(Exception)
async def _any_exc(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "INTERNAL", "next_action": "Retry; if it persists, report the study id."})


@app.middleware("http")
async def _limits_and_headers(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BODY:
        return JSONResponse(status_code=413, content={"error": "BODY_TOO_LARGE", "next_action": "Send a body under 256 KB."})
    if EXPECTED_ORIGINS and request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/"):
        origin = (request.headers.get("origin") or "").rstrip("/")
        if origin not in EXPECTED_ORIGINS:
            return JSONResponse(status_code=403, content={"error": "ORIGIN_REJECTED", "next_action": "Use the application from its own page."})
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    if not request.url.path.startswith("/api/"):
        resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: blob: https://tile.openstreetmap.org; style-src 'self' 'unsafe-inline'; worker-src 'self' blob:; connect-src 'self'"
    return resp


def session_of(request: Request, response: Response) -> str:
    tok = request.cookies.get(SESSION_COOKIE)
    if not tok or len(tok) < 16:
        tok = secrets.token_urlsafe(24)
        response.set_cookie(SESSION_COOKIE, tok, httponly=True, samesite="strict", secure=COOKIE_SECURE, max_age=86400)
    return tok


def load_study(sid: str, request: Request, response: Response) -> Study:
    sess = session_of(request, response)
    st = store.get(sid, sess)
    if st is None:
        raise err(404, "STUDY_EXPIRED", "Create a new study; studies live 30 minutes in memory and are lost on restart.")
    if st == "forbidden":
        raise err(403, "FORBIDDEN", "This study belongs to another session.")
    return st


# ----- schemas (closed) -----
class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateStudy(Closed):
    address: str = Field(min_length=3, max_length=120)
    storey: int = Field(ge=1, le=60)


class PlacementIn(Closed):
    facade: Literal["NE", "NW", "SW", "SE"]
    stack_position: Literal["end", "inner"] = "end"
    variant: Literal["A", "B", "C"] = "A"
    mirrored: bool = False
    openings: dict[str, bool] = Field(default_factory=dict)


class SurveyIn(Closed):
    """A survey is an analysis of a staged placement that nobody has confirmed. Every number it returns is labelled."""
    address: str = Field(min_length=3, max_length=120)
    storey: int = Field(ge=1, le=60)
    facade: Literal["NE", "NW", "SW", "SE"]
    stack_position: Literal["end", "inner"] = "end"
    variant: Literal["A", "B", "C"] = "A"
    mirrored: bool = False
    grid_spacing_m: Literal[0.1, 0.25, 0.5] = 0.5


class ChallengeIn(Closed):
    placement_revision: int


class ConfirmIn(Closed):
    placement_revision: int
    challenge: str = Field(min_length=8, max_length=64)


class AnalysisIn(Closed):
    grid_spacing_m: Literal[0.1, 0.25, 0.5] = 0.25


# ----- helpers -----
def placement_obj(st: Study) -> Placement:
    p = st.placement
    return Placement(storey=st.storey, facade=p["facade"], stack_position=p["stack_position"], variant=p["variant"], mirrored=p["mirrored"], openings=p["openings"])


def study_view(st: Study) -> dict:
    return {
        "study_id": st.id, "state": st.state, "address": st.address, "block": st.block, "storey": st.storey,
        "placement": st.placement, "placement_revision": st.placement_revision, "confirmed_revision": st.confirmed_revision,
        "plate_summary": {"recipe": PLATE.id, "digest": PLATE.digest()[:16], "storeys": PLATE.storeys, "sky_gardens": PLATE.sky_garden_storeys, "wings": [w.id for w in PLATE.wings], "limitations": PLATE.limitations},
        "provenance": {"footprint": "sourced (HDB Existing Building, Singapore Open Data Licence v1.0)", "storeys": "sourced (HDB Property Information)", "plate_storey_30": "inferred (no published plan; band symmetry)", "unit_plan": "published typical 4R plan; placement assumed until resident confirms", "heights": "assumed model 3.6/2.8/5.6 m reconciled to 147.8 m"},
        "result_digest": st.result["digest"] if st.result else None,
        "next_action": next_action(st),
    }


def next_action(st: Study) -> str:
    return {"created": "Propose a placement (facade, stack position, variant).", "placed": "Confirm the placement with a visible click in the page.", "needs_confirmation": "Confirm the placement with a visible click in the page.", "ready": "Run the solar analysis.", "analysing": "Wait for the analysis to finish.", "analysed": "Show the analysis, explain evidence, or export."}[st.state]


def plan_north(frame) -> tuple[float, float]:
    """True north expressed in the unit plan frame (x along the frontage, y inward), as a unit vector."""
    ax, ay = math.cos(frame.axis_rad), math.sin(frame.axis_rad)
    ix, iy = math.cos(frame.inward_rad), math.sin(frame.inward_rad)
    det = ax * iy - ay * ix
    u = (0 * iy - 1 * ix) / det      # solve u*A + v*I = (0, 1)
    v = (ax * 1 - ay * 0) / det
    if frame.mirrored:
        u = -u
    n = math.hypot(u, v) or 1.0
    return (u / n, v / n)


def build_exports(st: Study) -> None:
    pl = placement_obj(st)
    unit = UNITS[pl.variant]
    scene = build_scene(PRECINCT, PLATE, unit, pl)
    glb = write_glb(scene)
    obj = write_obj(scene.analytical_mesh())
    evidence = (canonical_json(st.result) + "\n").encode("utf-8")
    cards = cards_bundle(st.result, unit.envelope, north=plan_north(unit_frame(PLATE, pl)), rooms=unit.rooms).encode("utf-8")
    st.scene_glb = glb
    st.exports = {"scene.glb": glb, "analytical.obj": obj, "evidence.json": evidence, "cards.svg": cards}


def _run(st: Study, spacing: float):
    pl = placement_obj(st)
    return run_analysis(PRECINCT, PLATE, UNITS[pl.variant], pl, spacing)


# ----- routes -----
@app.get("/healthz")
def healthz():
    from ai_solar.radiance_env import RADIANCE_HOME
    return {"ok": True, "studies": store.count(), "radiance": bool(RADIANCE_HOME), "version": "2.0.0"}


@app.get("/api/context")
def context(request: Request, response: Response):
    session_of(request, response)
    return {"fixture_version": PRECINCT["fixture_version"], "frame": PRECINCT["coordinate_frame"], "supported": SUPPORTED,
            "buildings": [{k: b[k] for k in ("id", "block", "address", "development", "footprint", "height_m", "height_state", "max_floor_level", "sky_garden_storeys")} for b in PRECINCT["buildings"]],
            "plate": PLATE.model_dump(mode="json", by_alias=True), "units": {v: u.model_dump(mode="json", by_alias=True) for v, u in UNITS.items()},
            "opacity_tokens": {"context": 0.16, "tower": 0.28, "home": 1.0, "glass": 0.35}, "licence": PRECINCT["licence"]}


_CONTEXT_GLB: bytes | None = None


@app.get("/api/context/scene.glb")
def context_scene():
    """Precinct-only scene (sourced footprints extruded, target tower as bands) for the opening view."""
    global _CONTEXT_GLB
    if _CONTEXT_GLB is None:
        from ai_geometry.build import Box, Scene, neighbour_boxes
        from shapely.geometry import Polygon
        boxes = neighbour_boxes(PRECINCT, PLATE.block)
        fp = list(Polygon(PLATE.footprint).exterior.coords[:-1]); core = list(Polygon(PLATE.core).exterior.coords[:-1])
        for b in PLATE.bands:
            poly = core if b.kind in ("sky_garden", "roof") else fp
            boxes.append(Box(f"plate-{b.id}", "slab", poly, b.base_m, b.top_m, True, "tower", {"element": "plate", "state": "inferred"}))
        _CONTEXT_GLB = write_glb(Scene(boxes=boxes, placement=Placement(storey=PRECINCT["target"]["demo_storey"])))
    return Response(content=_CONTEXT_GLB, media_type="model/gltf-binary")


@app.post("/api/studies", status_code=201)
def create_study(body: CreateStudy, request: Request, response: Response):
    sess = session_of(request, response)
    target = next((s for s in SUPPORTED if body.address.strip().lower() in (s["address"].lower(), s["postal_code"])), None)
    if target is None:
        raise err(404, "FIXTURE_NOT_FOUND", "Use list_supported_homes; v2 covers 87 Dawson Road (141087).")
    lo, hi = target["storey_range"]
    if not (lo <= body.storey <= hi):
        raise err(422, "STOREY_OUT_OF_RANGE", f"Choose a storey between {lo} and {hi}.")
    st = store.create(sess, target["address"], target["block"], body.storey)
    return {"study_id": st.id, "state": st.state, "next_action": next_action(st)}


@app.get("/api/studies/{sid}")
def get_study(sid: str, request: Request, response: Response):
    return study_view(load_study(sid, request, response))


@app.put("/api/studies/{sid}/placement")
def put_placement(sid: str, body: PlacementIn, request: Request, response: Response):
    st = load_study(sid, request, response)
    unit = UNITS[body.variant]
    known = {e.id for e in unit.elements if e.kind in ("opening", "balcony", "railing", "ledge")}
    bad = [k for k in body.openings if k not in known]
    if bad:
        raise err(422, "PLACEMENT_INVALID", f"Unknown openings {bad}; use ids from the unit recipe.")
    try:
        unit_frame(PLATE, Placement(storey=st.storey, facade=body.facade, stack_position=body.stack_position))
    except ValueError as e:
        raise err(422, "PLACEMENT_INVALID", str(e))
    st.placement = body.model_dump()
    st.placement_revision += 1
    st.state = "needs_confirmation"
    st.result = None
    st.exports = {}
    return {"state": st.state, "placement_revision": st.placement_revision, "next_action": next_action(st)}


@app.post("/api/studies/{sid}/confirmation-challenge")
def challenge(sid: str, body: ChallengeIn, request: Request, response: Response, x_user_activation: str | None = Header(default=None)):
    st = load_study(sid, request, response)
    if st.placement is None:
        raise err(409, "CONFIRMATION_REQUIRED", "Propose a placement first.")
    if body.placement_revision != st.placement_revision:
        raise err(409, "STALE_CONFIRMATION", "The placement changed; review it and confirm again.")
    if x_user_activation != "trusted":
        raise err(403, "CONFIRMATION_REQUIRED", "Confirmation must come from a visible click in the page (X-User-Activation: trusted).")
    tok = secrets.token_urlsafe(18)
    st.challenge = (tok, time.time() + CHALLENGE_TTL, st.placement_revision)
    return {"challenge": tok, "expires_in_seconds": CHALLENGE_TTL}


@app.post("/api/studies/{sid}/confirmation")
def confirm(sid: str, body: ConfirmIn, request: Request, response: Response):
    st = load_study(sid, request, response)
    if body.placement_revision != st.placement_revision:
        raise err(409, "STALE_CONFIRMATION", "The placement changed; review it and confirm again.")
    ch = st.challenge
    st.challenge = None  # single use
    if ch is None or ch[0] != body.challenge or ch[1] < time.time() or ch[2] != body.placement_revision:
        raise err(403, "CONFIRMATION_REQUIRED", "Challenge missing, expired or already used; click confirm again.")
    st.confirmed_revision = st.placement_revision
    st.state = "ready"
    return {"state": st.state, "confirmed_revision": st.confirmed_revision, "next_action": next_action(st)}


@app.post("/api/studies/{sid}/analysis")
def analysis(sid: str, request: Request, response: Response, body: AnalysisIn = Body(default=AnalysisIn())):
    st = load_study(sid, request, response)
    if st.confirmed_revision is None or st.confirmed_revision != st.placement_revision:
        raise err(409, "CONFIRMATION_REQUIRED" if st.confirmed_revision is None else "STALE_CONFIRMATION", "Confirm the current placement with a visible click first.")
    if st.state == "analysed" and st.result is not None:
        return {"state": st.state, "digest": st.result["digest"], "cached": True, "next_action": next_action(st)}
    if not store.allow_analysis(st.session):
        raise err(429, "RATE_LIMITED", "Five analyses per ten minutes per session; wait and retry.")
    if not _analysis_lock.acquire(blocking=False):
        raise err(409, "ANALYSIS_BUSY", "Another analysis is running; retry in a few seconds.")
    try:
        st.state = "analysing"
        fut = _executor.submit(_run, st, float(body.grid_spacing_m))
        try:
            st.result = fut.result(timeout=ANALYSIS_TIMEOUT_S)
            timing = st.result.pop("_timing_s", None)
        except concurrent.futures.TimeoutError:
            st.state = "ready"
            raise err(504, "ANALYSIS_TIMEOUT", "The 15 s worker budget was exceeded; try a coarser grid.")
        build_exports(st)
        st.state = "analysed"
        return {"state": st.state, "digest": st.result["digest"], "timing_s": timing, "next_action": next_action(st)}
    finally:
        _analysis_lock.release()


@app.post("/api/survey")
def survey(body: SurveyIn, request: Request, response: Response):
    """Agent-only exploration. No study is created, nothing is confirmed, no report can come from it.
    The result carries provenance 'survey_unconfirmed' on every number so it can never pass as a confirmed study."""
    sess = session_of(request, response)
    target = next((s for s in SUPPORTED if body.address.strip().lower() in (s["address"].lower(), s["postal_code"])), None)
    if target is None:
        raise err(404, "FIXTURE_NOT_FOUND", "Use list_supported_homes; v2 covers 87 Dawson Road (141087).")
    lo, hi = target["storey_range"]
    if not (lo <= body.storey <= hi):
        raise err(422, "STOREY_OUT_OF_RANGE", f"Choose a storey between {lo} and {hi}.")
    ok, remaining, reset = store.allow_survey(sess)
    if not ok:
        raise err(429, "RATE_LIMITED", f"Thirty surveys per ten minutes per session; the oldest expires in {reset} s. Studies have their own budget of five.")
    if not _analysis_lock.acquire(blocking=False):
        raise err(409, "ANALYSIS_BUSY", "Another analysis is running; retry in a few seconds.")
    try:
        pl = Placement(storey=body.storey, facade=body.facade, stack_position=body.stack_position, variant=body.variant, mirrored=body.mirrored, openings={})
        fut = _executor.submit(lambda: run_analysis(PRECINCT, PLATE, UNITS[pl.variant], pl, float(body.grid_spacing_m)))
        try:
            r = fut.result(timeout=ANALYSIS_TIMEOUT_S)
        except concurrent.futures.TimeoutError:
            raise err(504, "ANALYSIS_TIMEOUT", "The 15 s worker budget was exceeded; try a coarser grid.")
        timing = r.pop("_timing_s", None)
        rad = r["radiation"]
        return {
            "mode": "survey", "provenance": "survey_unconfirmed",
            "label": "Survey, unconfirmed. Nobody has vouched for this placement; it is not a study and cannot produce a report.",
            "address": target["address"], "storey": body.storey,
            "placement": {"facade": body.facade, "stack_position": body.stack_position, "variant": body.variant, "mirrored": body.mirrored},
            "grid_spacing_m": body.grid_spacing_m, "digest": r["digest"], "method_version": r["method_version"], "timing_s": timing,
            "budget": {"surveys_remaining_in_window": remaining, "window_s": 600},
            "radiation": {"min": rad["min"], "avg": rad["avg"], "max": rad["max"], "unit": "kWh/m2 per year", "per_room": rad.get("per_room", {})},
            "next_action": "To keep any of this, create a study for the unit you will live in and confirm it with the visible button.",
        }
    finally:
        _analysis_lock.release()


@app.get("/api/studies/{sid}/result")
def result(sid: str, request: Request, response: Response):
    st = load_study(sid, request, response)
    if st.result is None:
        raise err(409, "EXPORT_NOT_READY", "Run the analysis first.")
    return st.result


@app.get("/api/studies/{sid}/scene.glb")
def scene_glb(sid: str, request: Request, response: Response):
    st = load_study(sid, request, response)
    if st.placement is None:
        raise err(409, "PLACEMENT_REQUIRED", "Propose a placement first.")
    if st.scene_glb is None or st.result is None:
        pl = placement_obj(st)
        st.scene_glb = write_glb(build_scene(PRECINCT, PLATE, UNITS[pl.variant], pl))
    return Response(content=st.scene_glb, media_type="model/gltf-binary")


@app.get("/api/studies/{sid}/export/{name}")
def export(sid: str, name: str, request: Request, response: Response):
    st = load_study(sid, request, response)
    if st.result is None:
        raise err(409, "EXPORT_NOT_READY", "Run the analysis first.")
    if not st.exports:
        build_exports(st)
    media = {"scene.glb": "model/gltf-binary", "analytical.obj": "text/plain", "evidence.json": "application/json", "cards.svg": "image/svg+xml", "scene.3dm": "application/octet-stream", "bundle.zip": "application/zip"}
    if name not in media:
        raise err(404, "EXPORT_UNKNOWN", f"Choose one of {sorted(media)}.")
    if name == "scene.3dm" and name not in st.exports:
        pl = placement_obj(st)
        st.exports[name] = write_3dm(build_scene(PRECINCT, PLATE, UNITS[pl.variant], pl))
    if name == "bundle.zip":
        data = zip_bundle(st)
    else:
        data = st.exports[name]
    if len(data) > MAX_EXPORT:
        raise err(413, "EXPORT_TOO_LARGE", "Export exceeds 20 MB.")
    return Response(content=data, media_type=media[name], headers={"Content-Disposition": f'attachment; filename="apartment-intelligence-{st.id}-{name}"'})


def zip_bundle(st: Study) -> bytes:
    if "scene.3dm" not in st.exports:
        pl = placement_obj(st)
        st.exports["scene.3dm"] = write_3dm(build_scene(PRECINCT, PLATE, UNITS[pl.variant], pl))
    files = dict(sorted(st.exports.items()))
    manifest = {"schema": "apartment-intelligence.manifest.v1", "study_digest": st.result["digest"], "method_version": st.result["method_version"], "files": {k: {"sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v)} for k, v in files.items()}, "note": "PNG/PDF renders are presentation only; SVG cards, GLB, OBJ and evidence.json are digest-bound and byte-stable; scene.3dm embeds fresh object GUIDs and is not byte-stable."}
    files["manifest.json"] = (canonical_json(manifest) + "\n").encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k in sorted(files):
            zi = zipfile.ZipInfo(k, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, files[k])
    return buf.getvalue()


# ----- static web -----
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = WEB_DIST / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(WEB_DIST / "index.html")
