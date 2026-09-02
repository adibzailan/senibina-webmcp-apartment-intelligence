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
        [-7.071, 0], [0, -7.071], [7.071, 0], [0, 7.071], [-7.071, 0]
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
                    assert str(exc) in {"PROPOSAL_OUTSIDE_FOOTPRINT", "APERTURE_DOES_NOT_FIT"}
                    continue
                assert plate["normal"][0] * cardinal[0] + plate["normal"][1] * cardinal[1] >= math.cos(math.pi / 4)


def test_plate_masks_cells_outside_an_l_shaped_footprint() -> None:
    target = _scene([])["target"]
    target["width"] = 10
    target["depth"] = 8
    target["building"]["footprint"] = [
        [-5, -5], [5, -5], [5, 0], [0, 0], [0, 5], [-5, 5], [-5, -5]
    ]

    plate = analysis.derive_plate(target)

    assert 0 < sum(plate["mask"]) < len(plate["mask"])
    assert plate["sensor_count"] == sum(plate["mask"])
    assert plate["usable_area_m2"] < target["width"] * target["depth"]


def test_depth_changes_the_canonical_result_digest() -> None:
    shallow = _scene([])
    deep = _scene([])
    deep["target"]["depth"] = 8

    assert analyse_scene(shallow)["digest"] != analyse_scene(deep)["digest"]


def test_masked_cells_do_not_dilute_radiation_summary() -> None:
    scene = _scene([])
    scene["target"]["width"] = 10
    scene["target"]["depth"] = 8
    scene["target"]["building"]["footprint"] = [
        [-5, -5], [5, -5], [5, 0], [0, 0], [0, 5], [-5, 5], [-5, -5]
    ]

    result = analyse_scene(scene)
    values = [value for value, mask in zip(result["radiation"]["sensor_values_kwh_m2"], result["plate"]["mask"]) if mask]

    assert result["radiation"]["average_kwh_m2"] == round(sum(values) / len(values), 2)
    assert result["radiation"]["minimum_kwh_m2"] == min(values)


def test_direct_sun_penetration_is_limited_by_the_window_head() -> None:
    target = _scene([])["target"]
    target["storey"] = 1
    plate = analysis.derive_plate(target)
    direction = Vector3D(math.cos(math.pi / 4), 0, math.sin(math.pi / 4))

    within_head = Point3D(3.0, 0, plate["elevation_m"])
    beyond_head = Point3D(2.7, 0, plate["elevation_m"])

    assert analysis._aperture_hit(within_head, direction, plate) is not None
    assert analysis._aperture_hit(beyond_head, direction, plate) is None


def test_diffuse_aperture_factor_decreases_with_floor_depth() -> None:
    target = _scene([])["target"]
    target["storey"] = 1
    plate = analysis.derive_plate(target)

    near = analysis._diffuse_view_factor(Point3D(4.5, 0, plate["elevation_m"]), plate, [])
    far = analysis._diffuse_view_factor(Point3D(0.0, 0, plate["elevation_m"]), plate, [])

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

    assert result["method_version"] == "apartment-intelligence-solar-v4"
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
            "width": 8,
            "depth": 6,
            "window_width": 4,
            "window_height": 1.2,
            "sill_height": 0.9,
            "building": {
                "id": "target",
                "footprint": [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]],
                "height_m": 120,
            },
        },
        "buildings": buildings,
    }
