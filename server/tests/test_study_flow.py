from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app


client = TestClient(app, base_url="https://testserver")


def create_study() -> tuple[str, str]:
    response = client.post(
        "/api/studies",
        json={"address": "87 Dawson Road", "storey": 30},
    )
    assert response.status_code == 201
    return response.json()["study_id"], response.cookies["study_session"]


def confirm_study(study_id: str, revision: int):
    receipt = client.post(
        f"/api/studies/{study_id}/confirmation-challenge",
        headers={"X-User-Activation": "trusted"},
        json={"proposal_revision": revision},
    )
    assert receipt.status_code == 200
    return client.post(
        f"/api/studies/{study_id}/confirmation",
        json={"proposal_revision": revision, "challenge": receipt.json()["challenge"]},
    )


def test_analysis_requires_visible_confirmation() -> None:
    study_id, _ = create_study()
    state = client.get(f"/api/studies/{study_id}").json()
    assert state["proposal"]["depth"] == 6.0
    assert state["plate_summary"]["sensor_count"] > 0
    assert set(state["plate_summary"]) == {"usable_area_m2", "sensor_count", "spacing_m", "normal_state"}
    response = client.post(f"/api/studies/{study_id}/analysis")
    assert response.status_code == 409
    assert response.json()["error"] == "CONFIRMATION_REQUIRED"


def test_confirmation_requires_a_revision_bound_single_use_challenge() -> None:
    study_id, _ = create_study()
    revision = client.get(f"/api/studies/{study_id}").json()["proposal_revision"]
    forged = client.post(
        f"/api/studies/{study_id}/confirmation",
        headers={"X-User-Activation": "trusted"},
        json={"proposal_revision": revision, "challenge": "x" * 43},
    )
    assert forged.status_code == 403
    receipt = client.post(
        f"/api/studies/{study_id}/confirmation-challenge",
        headers={"X-User-Activation": "trusted"},
        json={"proposal_revision": revision},
    ).json()["challenge"]
    assert client.post(f"/api/studies/{study_id}/confirmation", json={"proposal_revision": revision, "challenge": receipt}).status_code == 200
    assert client.post(f"/api/studies/{study_id}/confirmation", json={"proposal_revision": revision, "challenge": receipt}).status_code == 403


def test_confirmation_is_bound_to_proposal_revision() -> None:
    study_id, _ = create_study()
    proposal = client.put(
        f"/api/studies/{study_id}/proposal",
        json={"facade": "east", "position": "centre", "width": 8.0,
              "depth": 6.0, "window_width": 4.0, "window_height": 1.2, "sill_height": 0.9},
    )
    revision = proposal.json()["proposal_revision"]
    assert confirm_study(study_id, revision).status_code == 200
    client.put(
        f"/api/studies/{study_id}/proposal",
        json={"facade": "east", "position": "left", "width": 8.0,
              "depth": 8.0, "window_width": 4.0, "window_height": 1.2, "sill_height": 0.9},
    )
    response = client.post(f"/api/studies/{study_id}/analysis")
    assert response.status_code == 409
    assert response.json()["error"] == "STALE_CONFIRMATION"


def test_unknown_input_fields_are_rejected() -> None:
    response = client.post(
        "/api/studies",
        json={"address": "87 Dawson Road", "storey": 30, "confirmed": True},
    )
    assert response.status_code == 422


def test_fixture_and_storey_errors_are_structured() -> None:
    missing = client.post("/api/studies", json={"address": "1 Nowhere", "storey": 10})
    assert missing.status_code == 404
    assert missing.json()["error"] == "FIXTURE_NOT_FOUND"
    high = client.post("/api/studies", json={"address": "87 Dawson Road", "storey": 60})
    assert high.status_code == 422
    assert high.json()["error"] == "STOREY_OUT_OF_RANGE"


def test_confirmed_study_completes_and_exports_3dm() -> None:
    output_dir = Path(__file__).parents[2] / "outputs"
    before = set(output_dir.glob("*.3dm")) if output_dir.exists() else set()
    study_id, _ = create_study()
    state = client.get(f"/api/studies/{study_id}").json()
    confirmed = confirm_study(study_id, state["proposal_revision"])
    assert confirmed.status_code == 200
    analysed = client.post(f"/api/studies/{study_id}/analysis")
    assert analysed.status_code == 200
    assert len(analysed.json()["digest"]) == 64
    model = client.get(f"/api/studies/{study_id}/export.3dm")
    assert model.status_code == 200
    assert model.content[:4] == b"3D G"
    assert (set(output_dir.glob("*.3dm")) if output_dir.exists() else set()) == before
