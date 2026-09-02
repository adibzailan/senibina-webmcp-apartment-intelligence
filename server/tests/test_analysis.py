from app.analysis import analyse_scene, solar_altitude


def test_singapore_equinox_solar_noon_is_near_zenith() -> None:
    assert 88 <= solar_altitude(1.2903, 103.8519, "2026-03-21T13:10:00+08:00") <= 90


def test_duplicate_inputs_produce_identical_digest() -> None:
    scene = _scene([])
    assert analyse_scene(scene)["digest"] == analyse_scene(scene)["digest"]


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
    assert set(shadow["15:00"]["sensor_values"]) == {1}
    assert all(value * 2 == int(value * 2) for value in access["sensor_hours"])
    assert access["sensor_hours"] != clear["sensor_hours"]


def test_analysis_returns_computed_shadow_access_and_radiation_values() -> None:
    result = analyse_scene(_scene([]))

    assert result["method_version"] == "apartment-intelligence-solar-v3"
    assert len(result["shadow"]["samples"]) == 3
    assert all("sunlit_fraction" in sample for sample in result["shadow"]["samples"])
    assert all(len(sample["sensor_values"]) == 16 * 8 for sample in result["shadow"]["samples"])
    for sample in result["shadow"]["samples"]:
        assert round(sum(sample["sensor_values"]) / len(sample["sensor_values"]), 4) == sample["sunlit_fraction"]
    assert all(study["interval_minutes"] == 30 for study in result["solar_access"].values())
    assert all(len(study["sensor_hours"]) == 16 * 8 for study in result["solar_access"].values())
    for study in result["solar_access"].values():
        assert abs(sum(study["sensor_hours"]) / len(study["sensor_hours"]) - study["total_hours"]) < 0.002
    assert len(result["radiation"]["sensor_values_kwh_m2"]) == 16 * 8
    assert result["radiation"]["maximum_kwh_m2"] >= result["radiation"]["average_kwh_m2"] >= 0
    assert result["weather"]["sha256"] == "9293635032609058428c34809b0c2fa90178cb73d2aaf857f0918b46893bf60c"


def _scene(buildings: list[dict]) -> dict:
    return {
        "target": {
            "facade": "east",
            "storey": 30,
            "position": "centre",
            "width": 8,
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
