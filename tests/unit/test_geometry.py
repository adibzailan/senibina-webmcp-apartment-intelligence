import json

import pytest
from shapely.geometry import Polygon

from ai_geometry.build import Placement, build_scene, sensor_grid, unit_frame
from ai_geometry.schema import UnitRecipe
from ai_geometry.writers import write_glb, write_obj


def test_variants_share_envelope(units):
    envs = {v: tuple(map(tuple, u.envelope)) for v, u in units.items()}
    assert len(set(envs.values())) == 1


def test_envelope_area_near_published(units):
    area = Polygon(units["a"].envelope).area
    assert 85.0 <= area <= 96.0, area  # 87 m2 published floor area; envelope is gross


def test_analytical_mesh_watertight_and_glb_deterministic(precinct, plate, units, placement):
    sc = build_scene(precinct, plate, units["a"], placement)
    m = sc.analytical_mesh()
    assert m.is_watertight and m.is_winding_consistent
    assert write_glb(sc) == write_glb(build_scene(precinct, plate, units["a"], placement))


def test_glb_reload_preserves_home_wall_volume(precinct, plate, units, placement):
    import io
    import trimesh

    sc = build_scene(precinct, plate, units["a"], placement)
    home = [b for b in sc.boxes if b.opacity_token == "home" and b.blocks_sun]
    v_expected = sum(b.mesh().volume for b in home)
    loaded = trimesh.load(io.BytesIO(write_glb(sc)), file_type="glb")
    v_loaded = sum(g.volume for name, g in loaded.geometry.items() if any(name == b.id for b in home))
    assert abs(v_loaded - v_expected) / v_expected < 0.01


def test_every_kind_present(precinct, plate, units, placement):
    kinds = {b.kind for b in build_scene(precinct, plate, units["a"], placement).boxes}
    assert {"wall", "column", "opening", "slab", "balcony", "ledge", "overhang", "core", "railing"} <= kinds


def test_placement_outside_plate_invalid(plate, placement):
    with pytest.raises(ValueError, match="PLACEMENT_INVALID"):
        unit_frame(plate, Placement(storey=30, facade="XX"))
    with pytest.raises(ValueError, match="PLACEMENT_INVALID"):
        unit_frame(plate, Placement(storey=30, facade="NE", stack_position="middle"))


def test_unit_sits_inside_footprint(precinct, plate, units):
    fp = Polygon(plate.footprint).buffer(0.6)
    for facade in ("NE", "NW", "SW", "SE"):
        for stack in ("end", "inner"):
            for mirrored in (False, True):
                f = unit_frame(plate, Placement(storey=30, facade=facade, stack_position=stack, mirrored=mirrored))
                env = Polygon(f.poly_to_world(units["a"].envelope))
                assert env.difference(fp).area < 0.5 * env.area, (facade, stack, mirrored, env.difference(fp).area)


def test_sensor_grid_quarter_metre(plate, units, placement):
    s = sensor_grid(units["a"], plate, placement, 0.25)
    assert s["grid"]["spacing_m"] == 0.25 and s["count"] > 1000
    assert set(s["room_ids"]) >= {"main_bedroom", "living_dining", "kitchen"}


def test_recipe_schema_is_closed():
    raw = json.loads(open("data/recipes/4r-type-a.recipe.json").read())
    raw["surprise"] = 1
    with pytest.raises(Exception):
        UnitRecipe.model_validate(raw)
