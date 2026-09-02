import math
import json
from pathlib import Path

from app import analysis
from ladybug_geometry.geometry3d import Point3D, Vector3D


analyse_scene = analysis.analyse_scene
solar_altitude = analysis.solar_altitude


def test_singapore_equinox_solar_noon_is_near_zenith() -> None:
    assert 88 <= solar_altitude(1.2903, 103.8519, "2026-03-21T13:10:00+08:00") <= 90


def test_duplicate_inputs_produce_identical_digest() -> None:
    scene = _scene([])
    assert analyse_scene(scene)["digest"] == analyse_scene(scene)["digest"]


def test_plate_snaps_to_a_real_rotated_facade_and_stays_horizontal() -> None:
    target = _scene([])["target"]
    target["building"]["footprint"] = [
        [-20, 0], [0, -20], [20, 0], [0, 20], [-20, 0]
    ]

    plate = analysis.derive_plate(target)

    assert plate["normal_state"] == "sourced_edge"
    assert math.isclose(math.hypot(*plate["normal"]), 1.0, abs_tol=1e-6)
    assert plate["normal"][0] > 0.65
    assert abs(plate["normal"][1]) > 0.65
    assert all(point[2] == plate["elevation_m"] for point in plate["outline_xyz"])


def test_dawson_fixture_never_resolves_a_successful_proposal_to_the_wrong_facade() -> None:
    fixture = json.loads((Path(__file__).parents[2] / "data" / "fixtures" / "dawson-v1.json").read_text())
    for building in fixture["buildings"]:
        for facade, cardinal in analysis.FACADE_NORMALS.items():
            for position in ("left", "centre", "right"):
                target = {**_scene([])["target"], "building": building, "facade": facade, "position": position,
                          "storey": min(30, building["max_floor_level"])}
                try:
                    plate = analysis.derive_plate(target)
                except ValueError as exc:
                    assert str(exc) in {"PLAN_PLACEMENT_OUTSIDE_FOOTPRINT", "APERTURE_DOES_NOT_FIT"}
                    continue
                assert plate["normal"][0] * cardinal[0] + plate["normal"][1] * cardinal[1] >= .5


def test_plan_is_never_clipped_into_a_fragment() -> None:
    target = _scene([])["target"]
    target["building"]["footprint"] = [
        [-5, -5], [5, -5], [5, 0], [0, 0], [0, 5], [-5, 5], [-5, -5]
    ]

    try:
        analysis.derive_plate(target)
    except ValueError as exc:
        assert str(exc) == "PLAN_PLACEMENT_OUTSIDE_FOOTPRINT"
    else:
        raise AssertionError("the fixed plan must be rejected instead of clipped")


def test_mirroring_changes_the_canonical_result_digest() -> None:
    regular = _scene([])
    mirrored = _scene([])
    mirrored["target"]["mirrored"] = True

    assert analyse_scene(regular)["digest"] != analyse_scene(mirrored)["digest"]


def test_compiled_plan_is_orthogonal_and_has_exact_reference_area() -> None:
    plate = analysis.derive_plate(_scene([])["target"])
    assert plate["plan"]["plan_id"] == "skyville-dawson-4r-type-a-base"
    assert plate["plan"]["source_state"] == "published_typical_reference"
    assert plate["reference_area_m2"] == 87.0
    assert math.isclose(plate["sampled_area_m2"], 87.0, abs_tol=2.0)
    assert len(plate["outline_xy"]) > 5
    assert plate["placement"]["containment_fraction"] >= .95


def test_direct_sun_penetration_is_limited_by_the_window_head() -> None:
    target = _scene([])["target"]
    target["storey"] = 1
    plate = analysis.derive_plate(target)
    normal = plate["normal"]
    direction = Vector3D(normal[0] * math.cos(math.pi / 4), normal[1] * math.cos(math.pi / 4), math.sin(math.pi / 4))
    anchor = plate["anchor_xy"]
    within_head = Point3D(anchor[0] - normal[0] * 2.0, anchor[1] - normal[1] * 2.0, plate["elevation_m"])
    beyond_head = Point3D(anchor[0] - normal[0] * 2.2, anchor[1] - normal[1] * 2.2, plate["elevation_m"])

    assert analysis._aperture_hit(within_head, direction, plate) is not None
    assert analysis._aperture_hit(beyond_head, direction, plate) is None


def test_diffuse_aperture_factor_decreases_with_floor_depth() -> None:
    target = _scene([])["target"]
    target["storey"] = 1
    plate = analysis.derive_plate(target)

    normal = plate["normal"]
    anchor = plate["anchor_xy"]
    near = analysis._diffuse_view_factor(Point3D(anchor[0] - normal[0], anchor[1] - normal[1], plate["elevation_m"]), plate, [])
    far = analysis._diffuse_view_factor(Point3D(anchor[0] - normal[0] * 5, anchor[1] - normal[1] * 5, plate["elevation_m"]), plate, [])

    assert 0 < far < near < 1


def test_eastern_obstruction_only_removes_morning_access() -> None:
    clear = analyse_scene(_scene([]))["solar_access"]["2026-03-21"]
    scene = _scene([
        {"id": "east", "footprint": [[20, -20], [40, -20], [40, 20], [20, 20], [20, -20]], "height_m": 300}
    ])
    result = analyse_scene(scene)
    access = result["solar_access"]["2026-03-21"]
    assert access["morning_hours"] < clear["morning_hours"]
    assert access["afternoon_hours"] == clear["afternoon_hours"]
    shadow = {sample["time"]: sample for sample in result["shadow"]["samples"]}
    assert set(shadow["09:00"]["sensor_values"]) == {0}
    assert set(shadow["15:00"]["sensor_values"]) == {0}
    assert all(value * 2 == int(value * 2) for value in access["sensor_hours"])
    assert access["sensor_hours"] != clear["sensor_hours"]


def test_analysis_returns_computed_shadow_access_and_radiation_values() -> None:
    result = analyse_scene(_scene([]))

    assert result["method_version"] == "apartment-intelligence-solar-v5"
    assert len(result["plate"]["plan"]["fixture_digest"]) == 64
    cells = result["plate"]["grid"][0] * result["plate"]["grid"][1]
    assert cells <= 256
    assert result["plate"]["sensor_count"] == sum(result["plate"]["mask"])
    assert len(result["shadow"]["samples"]) == 3
    assert all("sun_patch_area_m2" in sample for sample in result["shadow"]["samples"])
    assert all(len(sample["sensor_values"]) == cells for sample in result["shadow"]["samples"])
    for sample in result["shadow"]["samples"]:
        visible = [value for value, mask in zip(sample["sensor_values"], result["plate"]["mask"]) if mask]
        assert round(sum(visible) / len(visible), 4) == sample["sunlit_fraction"]
    assert all(study["interval_minutes"] == 30 for study in result["solar_access"].values())
    assert all(len(study["sensor_hours"]) == cells for study in result["solar_access"].values())
    for study in result["solar_access"].values():
        values = [value for value, mask in zip(study["sensor_hours"], result["plate"]["mask"]) if mask]
        assert abs(sum(values) / len(values) - study["total_hours"]) < 0.002
    assert len(result["radiation"]["sensor_values_kwh_m2"]) == cells
    assert result["radiation"]["maximum_kwh_m2"] >= result["radiation"]["average_kwh_m2"] >= 0
    assert "sensor-to-aperture configuration factor" in " ".join(result["radiation"]["components"])
    assert "no glazing transmittance" in result["radiation"]["limitations"]
    assert result["weather"]["sha256"] == "9293635032609058428c34809b0c2fa90178cb73d2aaf857f0918b46893bf60c"


def _scene(buildings: list[dict]) -> dict:
    return {
        "target": {
            "facade": "east",
            "storey": 30,
            "position": "centre",
            "mirrored": False,
            "window_width": 4,
            "window_height": 1.2,
            "sill_height": 0.9,
            "building": {
                "id": "target",
                "footprint": [[-12, -12], [12, -12], [12, 12], [-12, 12], [-12, -12]],
                "height_m": 120,
            },
        },
        "buildings": buildings,
    }
