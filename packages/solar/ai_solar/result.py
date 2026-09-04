"""Assemble the `apartment-intelligence.result.v6` record with evidence provenance and digest."""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np

from ai_geometry.build import Placement, Scene, build_scene, sensor_grid
from ai_geometry.schema import PlateRecipe, UnitRecipe, canonical_json, sha256_canonical

from . import METHOD_VERSION
from .sky import sky_matrix, sky_record
from .study import direct_sun_study, mesh3d_from_trimesh, radiation_study, shadow_instants
from .sunpath import sunpath_for, sunpath_record
from .weather import weather_record

RESULT_SCHEMA = "apartment-intelligence.result.v6"


def evidence(value, state, source_ref, method, confidence, limitation=None):
    return {"value": value, "state": state, "source_ref": source_ref, "method": method, "confidence": confidence, "limitation": limitation}


def run_analysis(precinct: dict, plate: PlateRecipe, unit: UnitRecipe, placement: Placement, spacing_m: float = 0.25, epw_path: str | None = None, include_direct_sun: bool = True, confirmation: str = "resident_confirmed") -> dict:
    """`confirmation` is how the placement was vouched for: "resident_confirmed" (a visible click) or
    "resident_delegated" (the resident clicked once to let their agent confirm; the agent then staged this placement).
    It is part of the record and therefore of the digest."""
    t0 = time.time()
    scene = build_scene(precinct, plate, unit, placement)
    amesh = scene.analytical_mesh()
    ctx = mesh3d_from_trimesh(amesh)
    sensors = sensor_grid(unit, plate, placement, spacing_m)
    sky = sky_matrix(epw_path)
    sp = sunpath_for(epw_path)
    rad = radiation_study(sky, sensors["xyz"], ctx)
    total = np.array(rad["total_kwh_m2"])
    rooms = sorted(set(sensors["room_ids"]))
    per_room = {}
    for r in rooms:
        idx = [i for i, rid in enumerate(sensors["room_ids"]) if rid == r]
        vals = total[idx]
        per_room[r] = {"sensors": len(idx), "min": round(float(vals.min()), 3), "avg": round(float(vals.mean()), 3), "max": round(float(vals.max()), 3)}
    sun = direct_sun_study(sp, sensors["xyz"], ctx) if include_direct_sun else {}
    shadows = shadow_instants(sp, sensors["xyz"], ctx)
    wr = weather_record(epw_path)
    recipe_digest = sha256_canonical({"plate": plate.digest(), "unit": unit.digest()})
    limitations = [
        "Sunlight is counted only when it reaches a point directly from the sky; light bouncing off walls, floors or neighbouring buildings is not included.",
        "Windows are treated as fully open to light; glass, frames, curtains and blinds would reduce the numbers.",
        "Numbers are measured on an imaginary surface 0.8 m above the floor, about table height, not on the floor itself.",
        "The shape of the tower above ground level and the heights of neighbouring blocks are estimated; window sizes and the balcony are assumptions you can change.",
    ] + list(unit.limitations) + list(plate.limitations)
    result = {
        "schema": RESULT_SCHEMA,
        "method_version": METHOD_VERSION,
        "engine": {"ladybug_core": "0.44.59", "ladybug_radiance": "0.2.12", "radiance": "6.1a 2026-05-05 LBNL (6.1.39b9966033)", "sky": "gendaymtx", "trace": "rcontrib -ab 0"},
        "weather": wr,
        "sky": sky_record(sky),
        "placement": placement.as_dict(),
        "recipe_digest": recipe_digest,
        "recipes": {"plate": plate.id, "unit": unit.id, "plate_digest": plate.digest(), "unit_digest": unit.digest()},
        "sensors": {**{k: v for k, v in sensors.items() if k != "xyz"}, "xyz": sensors["xyz"]},
        "sunpath": sunpath_record(sp),
        "shadow": {"instants": shadows},
        "solar_access": sun,
        "radiation": {"sensor_kwh_m2": rad["total_kwh_m2"], "components": {"direct": rad["direct_kwh_m2"], "diffuse": rad["diffuse_kwh_m2"], "ground": rad["ground_kwh_m2"]}, "per_room": per_room, "min": round(float(total.min()), 3), "avg": round(float(total.mean()), 3), "max": round(float(total.max()), 3), "unit": "kWh/m2 per year", "limitations": limitations},
        "provenance": [
            evidence(wr["annual_ghi_kwh_m2"], "sourced", wr["source"], "Yearly sunlight on open ground at Changi, from the typical-year weather file", "high", "A typical year assembled from 2011-2025 records, not a forecast"),
            evidence(placement.storey, confirmation, "resident selection" if confirmation == "resident_confirmed" else "resident delegation to agent", "Storey you chose in the page" if confirmation == "resident_confirmed" else "Storey staged by your agent under the delegation you granted in the page", "high", None if confirmation == "resident_confirmed" else "Confirmed by your agent, not by your own click; revoke the delegation in the page if that was not intended"),
            evidence(placement.facade, "assumed", plate.wings[0].source.document, "Wing you chose; which end of the wing is the 4-room flat is an assumption", "medium", "HDB has not published which end of each wing is the 4-room flat"),
            evidence(round(float(total.mean()), 3), "computed", METHOD_VERSION, "Average yearly sunlight across the sensor points, computed with Ladybug and Radiance", "medium", limitations[0]),
        ],
        "analytical_mesh": {"faces": int(len(amesh.faces)), "watertight": bool(amesh.is_watertight)},
        "confirmation": {"kind": confirmation},
    }
    result["digest"] = result_digest(result)
    result["_timing_s"] = round(time.time() - t0, 3)  # stripped by the API before storage
    return result


def result_digest(result: dict) -> str:
    body = {k: v for k, v in result.items() if k not in ("digest", "_timing_s")}
    return sha256_canonical({"recipe_digest": result["recipe_digest"], "placement": result["placement"], "weather_sha256": result["weather"]["sha256"], "method_version": result["method_version"], "result": body})
