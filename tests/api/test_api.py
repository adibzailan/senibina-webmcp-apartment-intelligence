import pytest
from fastapi.testclient import TestClient

from ai_api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _create(c, storey=30):
    r = c.post("/api/studies", json={"address": "87 Dawson Road", "storey": storey})
    assert r.status_code == 201, r.text
    return r.json()["study_id"]


def _place(c, sid, **kw):
    body = {"facade": "NE", "stack_position": "end", "variant": "A", "mirrored": False, "openings": {}}
    body.update(kw)
    return c.put(f"/api/studies/{sid}/placement", json=body)


def _confirm(c, sid, rev):
    ch = c.post(f"/api/studies/{sid}/confirmation-challenge", json={"placement_revision": rev}, headers={"X-User-Activation": "trusted"})
    assert ch.status_code == 200, ch.text
    return c.post(f"/api/studies/{sid}/confirmation", json={"placement_revision": rev, "challenge": ch.json()["challenge"]})


def test_context_and_supported(client):
    r = client.get("/api/context")
    assert r.status_code == 200 and r.json()["supported"][0]["postal_code"] == "141087"


def test_closed_schema_rejects_extra_and_confirmed_argument(client):
    sid = _create(client)
    assert _place(client, sid, confirmed=True).status_code == 422
    assert client.post("/api/studies", json={"address": "87 Dawson Road", "storey": 30, "confirmed": True}).status_code == 422


def test_storey_and_fixture_errors(client):
    assert client.post("/api/studies", json={"address": "1 Nowhere", "storey": 3}).json()["error"] == "FIXTURE_NOT_FOUND"
    assert client.post("/api/studies", json={"address": "87 Dawson Road", "storey": 55}).json()["error"] == "STOREY_OUT_OF_RANGE"


def test_analysis_requires_confirmation_and_challenge_is_single_use(client):
    sid = _create(client)
    assert client.post(f"/api/studies/{sid}/analysis").json()["error"] == "CONFIRMATION_REQUIRED"
    rev = _place(client, sid).json()["placement_revision"]
    assert client.post(f"/api/studies/{sid}/analysis").json()["error"] == "CONFIRMATION_REQUIRED"
    no_act = client.post(f"/api/studies/{sid}/confirmation-challenge", json={"placement_revision": rev})
    assert no_act.status_code == 403
    ch = client.post(f"/api/studies/{sid}/confirmation-challenge", json={"placement_revision": rev}, headers={"X-User-Activation": "trusted"}).json()["challenge"]
    assert client.post(f"/api/studies/{sid}/confirmation", json={"placement_revision": rev, "challenge": ch}).status_code == 200
    replay = client.post(f"/api/studies/{sid}/confirmation", json={"placement_revision": rev, "challenge": ch})
    assert replay.status_code == 403


def test_stale_revision_after_replacement(client):
    sid = _create(client)
    rev = _place(client, sid).json()["placement_revision"]
    assert _confirm(client, sid, rev).status_code == 200
    _place(client, sid, variant="B")
    r = client.post(f"/api/studies/{sid}/analysis")
    assert r.status_code == 409 and r.json()["error"] == "STALE_CONFIRMATION"
    assert client.post(f"/api/studies/{sid}/confirmation-challenge", json={"placement_revision": rev}, headers={"X-User-Activation": "trusted"}).json()["error"] == "STALE_CONFIRMATION"


def test_cross_session_forbidden_and_unknown_expired(client):
    sid = _create(client)
    other = TestClient(app)
    assert other.get(f"/api/studies/{sid}").status_code == 403
    assert client.get("/api/studies/does-not-exist").json()["error"] == "STUDY_EXPIRED"


def test_full_run_exports_and_determinism(client):
    sid = _create(client)
    rev = _place(client, sid).json()["placement_revision"]
    assert _confirm(client, sid, rev).status_code == 200
    r = client.post(f"/api/studies/{sid}/analysis", json={"grid_spacing_m": 0.5})
    assert r.status_code == 200, r.text
    digest = r.json()["digest"]
    res = client.get(f"/api/studies/{sid}/result").json()
    assert res["digest"] == digest and res["sensors"]["grid"]["spacing_m"] == 0.5
    glb = client.get(f"/api/studies/{sid}/export/scene.glb").content
    svg = client.get(f"/api/studies/{sid}/export/cards.svg").content
    z = client.get(f"/api/studies/{sid}/export/bundle.zip").content
    assert glb[:4] == b"glTF" and svg.startswith(b"<svg") and z[:2] == b"PK"
    # second identical study -> identical digest, GLB and SVG bytes
    sid2 = _create(client)
    rev2 = _place(client, sid2).json()["placement_revision"]
    _confirm(client, sid2, rev2)
    assert client.post(f"/api/studies/{sid2}/analysis", json={"grid_spacing_m": 0.5}).json()["digest"] == digest
    assert client.get(f"/api/studies/{sid2}/export/scene.glb").content == glb
    assert client.get(f"/api/studies/{sid2}/export/cards.svg").content == svg
    import io, zipfile
    z2 = client.get(f"/api/studies/{sid2}/export/bundle.zip").content
    a, b = zipfile.ZipFile(io.BytesIO(z)), zipfile.ZipFile(io.BytesIO(z2))
    assert a.namelist() == b.namelist() == ["analytical.obj", "cards.svg", "evidence.json", "manifest.json", "scene.3dm", "scene.glb"]
    for n in a.namelist():
        if n not in ("scene.3dm", "manifest.json"):  # 3DM embeds fresh GUIDs, so it and its manifest hash differ
            assert a.read(n) == b.read(n), n


def test_survey_is_labelled_and_never_confirms(client):
    """A survey analyses a staged placement with no study and no click; every number is labelled unconfirmed."""
    r = client.post("/api/survey", json={"address": "87 Dawson Road", "storey": 12, "facade": "NE", "stack_position": "end", "variant": "A", "grid_spacing_m": 0.5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "survey" and body["provenance"] == "survey_unconfirmed"
    assert "unconfirmed" in body["label"].lower() and "report" in body["label"].lower()
    assert body["radiation"]["avg"] >= 0 and len(body["digest"]) == 64
    # a survey leaves no study behind and rejects a confirmed flag like every other tool
    assert client.post("/api/survey", json={"address": "87 Dawson Road", "storey": 12, "facade": "NE", "confirmed": True}).status_code == 422
    assert client.post("/api/survey", json={"address": "1 Nowhere Road", "storey": 12, "facade": "NE"}).status_code == 404
