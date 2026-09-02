from pathlib import Path

import rhino3dm

from app.export_3dm import write_study_3dm


LAYERS = [
    "01_SOURCED_CONTEXT",
    "02_INFERRED_MASSING",
    "03_HUMAN_CONFIRMED_UNIT",
    "04_GENERATED_ANALYSIS",
    "05_RESULTS",
]


def test_3dm_round_trip_has_units_layers_and_metadata(tmp_path: Path) -> None:
    target = tmp_path / "study.3dm"
    building = {
        "id": "hdb-141087", "block": "87", "height_m": 141.0,
        "footprint": [[0, 0], [20, 0], [20, 10], [0, 10], [0, 0]],
        "footprint_state": "sourced", "height_state": "inferred",
    }
    plate = {
        "outline_xyz": [[20, 1, 87.02], [20, 9, 87.02], [14, 9, 87.02], [14, 1, 87.02], [20, 1, 87.02]],
        "anchor_xy": [20, 5], "wall_direction": [0, 1], "normal": [1, 0],
        "elevation_m": 87.02, "grid": [4, 3], "mask": [1] * 12,
        "sensor_xyz": [[19.25 - row * 1.5, 2 + col * 2, 87.02] for row in range(3) for col in range(4)],
        "aperture": {"centre_xyz": [20, 5, 88.5], "width_m": 4, "height_m": 1.2, "sill_m": .9},
    }
    write_study_3dm(target, {"digest": "abc", "buildings": [building],
                            "result": {"method_version": "apartment-intelligence-solar-v4", "plate": plate,
                                       "radiation": {"sensor_values_kwh_m2": list(range(12))}},
                            "target": {"building": building, "storey": 30, "facade": "east",
                                       "width": 8, "window_width": 4, "window_height": 1.2, "sill_height": .9}})
    model = rhino3dm.File3dm.Read(str(target))
    assert model.Settings.ModelUnitSystem == rhino3dm.UnitSystem.Meters
    assert [layer.Name for layer in model.Layers] == LAYERS
    assert model.Strings["digest"] == "abc"
    assert model.Strings["method"] == "apartment-intelligence-solar-v4"
    assert len(model.Objects) >= 5
    names = {obj.Attributes.Name for obj in model.Objects}
    assert "Human-confirmed usable apartment floor plate cell" in names
    assert "Generated horizontal radiation sensor mesh" in names
    assert {obj.Attributes.GetUserString("state") for obj in model.Objects} >= {
        "sourced", "inferred", "human-confirmed", "generated", "result"
    }
