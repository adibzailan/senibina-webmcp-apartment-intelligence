from __future__ import annotations

import json
import multiprocessing
import os
import secrets
import threading
import time
from pathlib import Path
from queue import Empty
from typing import Literal

from fastapi import Cookie, FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .analysis import analyse_scene, derive_plate
from .export_3dm import write_study_3dm


ROOT = Path(__file__).parents[2]
FIXTURE = json.loads((ROOT / "data" / "fixtures" / "dawson-v1.json").read_text())
BUILDINGS = {building["address"].lower(): building for building in FIXTURE["buildings"]}
TTL_SECONDS = 30 * 60
MAX_STUDIES = 100
app = FastAPI(title="Apartment Intelligence", docs_url=None, redoc_url=None)
studies: dict[str, dict] = {}
analysis_lock = threading.Lock()
analysis_history: dict[str, list[float]] = {}


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StudyInput(ClosedModel):
    address: str = Field(min_length=3, max_length=80)
    storey: int = Field(ge=1, le=60)


class ProposalInput(ClosedModel):
    facade: Literal["north", "east", "south", "west"]
    position: Literal["left", "centre", "right"]
    mirrored: bool = False
    window_width: float = Field(ge=0.5, le=12)
    window_height: float = Field(ge=0.5, le=3)
    sill_height: float = Field(ge=0, le=2)


class ConfirmationInput(ClosedModel):
    proposal_revision: int = Field(ge=1)
    challenge: str = Field(min_length=32, max_length=128)


class ConfirmationChallengeInput(ClosedModel):
    proposal_revision: int = Field(ge=1)


def error(code: str, status: int, next_action: str) -> JSONResponse:
    return JSONResponse({"error": code, "next_action": next_action}, status_code=status)


def get_study(study_id: str, session: str | None) -> dict | JSONResponse:
    study = studies.get(study_id)
    if not study or study["session"] != session or time.monotonic() - study["touched"] > TTL_SECONDS:
        return error("STUDY_EXPIRED", 404, "Create a new apartment study.")
    study["touched"] = time.monotonic()
    return study


def study_target(study: dict, proposal: dict | None = None) -> dict:
    return {**(proposal or study["proposal"]), "storey": study["storey"], "building": study["building"]}


def plate_summary(study: dict) -> dict:
    plate = derive_plate(study_target(study))
    return {
        "plan_id": plate["plan"]["plan_id"],
        "reference_area_m2": plate["reference_area_m2"],
        "sampled_area_m2": plate["sampled_area_m2"],
        "sensor_count": plate["sensor_count"],
        "spacing_m": plate["spacing_m"],
        "normal_state": plate["normal_state"],
        "mirrored": plate["placement"]["mirrored"],
        "placement_state": plate["placement"]["state"],
    }


def _analysis_worker(scene: dict, queue) -> None:
    queue.put(analyse_scene(scene))


def bounded_analysis(scene: dict) -> dict | None:
    context = multiprocessing.get_context("spawn")
    queue = context.Queue(1)
    process = context.Process(target=_analysis_worker, args=(scene, queue))
    process.start()
    try:
        # Drain the payload before joining. A per-sensor result can fill a
        # Windows pipe while the child flushes its queue, otherwise leaving
        # parent and child waiting for one another until the timeout.
        result = queue.get(timeout=15)
    except Empty:
        process.terminate(); process.join(2)
        return None
    process.join(2)
    if process.is_alive():
        process.terminate(); process.join(2)
        return None
    return result if process.exitcode == 0 else None


@app.middleware("http")
async def request_limit(request: Request, call_next):
    length = int(request.headers.get("content-length", "0") or 0)
    if length > 256 * 1024:
        return error("REQUEST_TOO_LARGE", 413, "Reduce the request below 256 KB.")
    origin = request.headers.get("origin")
    expected = os.getenv("EXPECTED_ORIGIN", "https://apartment.senibina.com.sg")
    development_origins = (
        {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"}
        if os.getenv("ALLOW_DEVELOPMENT_ORIGINS", "false").lower() == "true"
        else set()
    )
    if origin and origin not in {expected, *development_origins}:
        return error("ORIGIN_NOT_ALLOWED", 403, "Use the public Apartment Intelligence origin.")
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), tools=(self)"
    response.headers["Origin-Agent-Cluster"] = "?1"
    return response


@app.get("/api/healthz")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/context")
def context() -> dict:
    return {"fixture_version": FIXTURE["fixture_version"], "coordinate_frame": FIXTURE["coordinate_frame"],
            "height_basis": FIXTURE["height_basis"], "buildings": FIXTURE["buildings"]}


@app.post("/api/studies", status_code=201)
def create_study(payload: StudyInput, study_session: str | None = Cookie(default=None)):
    building = BUILDINGS.get(payload.address.strip().lower())
    if not building:
        return error("FIXTURE_NOT_FOUND", 404, "Choose an address in the Dawson fixture.")
    if payload.storey > building["max_floor_level"]:
        return error("STOREY_OUT_OF_RANGE", 422, f"Choose storey 1–{building['max_floor_level']}.")
    if len(studies) >= MAX_STUDIES:
        oldest = min(studies, key=lambda key: studies[key]["touched"])
        del studies[oldest]
    session = study_session or secrets.token_urlsafe(24)
    study_id = secrets.token_urlsafe(18)
    studies[study_id] = {
        "id": study_id,
        "session": session,
        "state": "needs_confirmation",
        "address": building["address"],
        "storey": payload.storey,
        "building": building,
        "proposal": {"facade": "east", "position": "centre", "mirrored": False,
                     "window_width": 4.0, "window_height": 1.2, "sill_height": 0.9},
        "proposal_revision": 1,
        "confirmed_revision": None,
        "confirmation_challenges": {},
        "touched": time.monotonic(),
    }
    response = JSONResponse({"study_id": study_id, "state": "needs_confirmation", "next_action": "Review and confirm the visible unit proposal."}, status_code=201)
    response.set_cookie("study_session", session, secure=os.getenv("COOKIE_SECURE", "true").lower() == "true", httponly=True, samesite="strict", max_age=TTL_SECONDS)
    return response


@app.get("/api/studies/{study_id}")
def study_state(study_id: str, study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    next_actions = {"needs_confirmation": "Confirm the visible proposal.", "ready": "Run solar analysis.",
                    "analysing": "Wait for the bounded analysis.", "complete": "Explore or export the completed analysis."}
    plate = derive_plate(study_target(study))
    return {"study_id": study_id, "state": study["state"], "address": study["address"],
            "storey": study["storey"], "proposal": study["proposal"],
            "plate_summary": plate_summary(study),
            "plate": plate,
            "proposal_revision": study["proposal_revision"],
            "source_state": "sourced", "height_state": "inferred",
            "next_action": next_actions[study["state"]]}


@app.put("/api/studies/{study_id}/proposal")
def propose(study_id: str, payload: ProposalInput, study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    proposal = payload.model_dump()
    try:
        derive_plate(study_target(study, proposal))
    except ValueError as failure:
        code = str(failure)
        next_action = "Choose a facade and position where the complete reference plan fits." if code == "PLAN_PLACEMENT_OUTSIDE_FOOTPRINT" else "Reduce the opening or choose another facade position."
        return error(code, 422, next_action)
    study["proposal"] = proposal
    study["proposal_revision"] += 1
    study["confirmation_challenges"] = {}
    study["state"] = "needs_confirmation"
    return {"study_id": study_id, "state": study["state"], "proposal_revision": study["proposal_revision"], "next_action": "Review and confirm the visible proposal."}


@app.post("/api/studies/{study_id}/confirmation-challenge")
def confirmation_challenge(study_id: str, payload: ConfirmationChallengeInput,
            x_user_activation: str | None = Header(default=None),
            study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    if x_user_activation != "trusted":
        return error("CONFIRMATION_REQUIRED", 403, "Use the visible Confirm this home button.")
    if payload.proposal_revision != study["proposal_revision"]:
        return error("STALE_CONFIRMATION", 409, "Review the latest visible proposal.")
    challenge = secrets.token_urlsafe(32)
    study["confirmation_challenges"] = {challenge: {
        "revision": payload.proposal_revision,
        "expires": time.monotonic() + 10,
    }}
    return {"challenge": challenge, "expires_in_seconds": 10}


@app.post("/api/studies/{study_id}/confirmation")
def confirm(study_id: str, payload: ConfirmationInput,
            study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    receipt = study["confirmation_challenges"].pop(payload.challenge, None)
    if not receipt or receipt["expires"] < time.monotonic():
        return error("CONFIRMATION_REQUIRED", 403, "Use the visible Confirm this home button again.")
    if payload.proposal_revision != study["proposal_revision"] or receipt["revision"] != payload.proposal_revision:
        return error("STALE_CONFIRMATION", 409, "Review the latest visible proposal.")
    study["confirmed_revision"] = payload.proposal_revision
    study["state"] = "ready"
    return {"study_id": study_id, "state": "ready", "next_action": "Run solar analysis."}


@app.post("/api/studies/{study_id}/analysis")
def run_analysis(study_id: str, study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    if study["confirmed_revision"] is None:
        return error("CONFIRMATION_REQUIRED", 409, "Confirm the visible unit proposal first.")
    if study["confirmed_revision"] != study["proposal_revision"]:
        return error("STALE_CONFIRMATION", 409, "Confirm the revised visible proposal.")
    now = time.monotonic()
    recent = [stamp for stamp in analysis_history.get(study["session"], []) if now - stamp < 600]
    if len(recent) >= 5:
        return error("ANALYSIS_BUSY", 429, "Wait before running another analysis.")
    if not analysis_lock.acquire(blocking=False):
        return error("ANALYSIS_BUSY", 409, "Wait for the active analysis to finish.")
    try:
        analysis_history[study["session"]] = recent + [now]
        study["state"] = "analysing"
        target = study_target(study)
        buildings = [
            {"id": building["id"], "footprint": building["footprint"], "height_m": building["height_m"]}
            for building in FIXTURE["buildings"]
        ]
        result = bounded_analysis({"target": target, "buildings": buildings})
        if result is None:
            study["state"] = "ready"
            return error("ANALYSIS_TIMEOUT", 504, "Try the bounded analysis again.")
        study["result"] = result
        study["state"] = "complete"
    finally:
        analysis_lock.release()
    return {"study_id": study_id, "state": "complete", "digest": study["result"]["digest"], "next_action": "Explore or export the completed analysis."}


@app.get("/api/studies/{study_id}/result")
def result(study_id: str, study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    if study["state"] != "complete":
        return error("EXPORT_NOT_READY", 409, "Complete the solar analysis first.")
    return study["result"]


@app.get("/api/studies/{study_id}/export.3dm")
def export_3dm(study_id: str, study_session: str | None = Cookie(default=None)):
    study = get_study(study_id, study_session)
    if isinstance(study, JSONResponse):
        return study
    if study["state"] != "complete":
        return error("EXPORT_NOT_READY", 409, "Complete the solar analysis first.")
    export_dir = ROOT / "outputs"
    export_dir.mkdir(exist_ok=True)
    path = export_dir / f"{study_id}.3dm"
    write_study_3dm(path, {"digest": study["result"]["digest"], "result": study["result"], "buildings": FIXTURE["buildings"],
                           "target": {**study["proposal"], "storey": study["storey"], "building": study["building"]}})
    if path.stat().st_size > 20 * 1024 * 1024:
        path.unlink(missing_ok=True)
        return error("EXPORT_NOT_READY", 413, "The export exceeded the 20 MB release limit.")
    return FileResponse(path, media_type="application/octet-stream", filename="apartment-intelligence.3dm",
                        background=BackgroundTask(path.unlink, missing_ok=True))


WEB_DIST = ROOT / "web" / "dist"
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
