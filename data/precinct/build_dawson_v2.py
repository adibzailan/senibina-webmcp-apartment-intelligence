"""Build data/precinct/dawson-v2.json from the sourced v1 footprints plus the v2 storey-height model.

Usage: .venv/bin/python data/precinct/build_dawson_v2.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ai_geometry.plate import FIRST_STOREY_M, ROOF_STRUCTURE_M, SKY_GARDENS, SKY_GARDEN_STOREY_M, TYPICAL_STOREY_M

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "data/fixtures/dawson-v1.json"
OUT = ROOT / "data/precinct/dawson-v2.json"

SKYVILLE = {"86", "87", "88"}
SKYTERRACE = {"89", "90", "91", "92", "93"}


def height_model(storeys: int, sky_gardens: list[int]) -> float:
    if storeys <= 1:
        return FIRST_STOREY_M
    h = FIRST_STOREY_M
    for s in range(2, storeys + 1):
        h += SKY_GARDEN_STOREY_M if s in sky_gardens else TYPICAL_STOREY_M
    return round(h, 3)


def main():
    v1 = json.loads(V1.read_text())
    buildings = []
    for b in v1["buildings"]:
        blk = b["block"]
        gardens = SKY_GARDENS if blk in SKYVILLE else []
        storeys = b["max_floor_level"]
        h = height_model(storeys, gardens)
        if blk in SKYVILLE:
            h = round(h + ROOF_STRUCTURE_M, 3)
        buildings.append({
            "id": b["id"], "block": blk, "address": b["address"], "postal_code": b["postal_code"],
            "development": "SkyVille @ Dawson" if blk in SKYVILLE else ("SkyTerrace @ Dawson" if blk in SKYTERRACE else "Dawson precinct"),
            "footprint": b["footprint"], "footprint_state": "sourced",
            "max_floor_level": storeys, "storeys_state": "sourced",
            "height_m": h, "height_state": "inferred",
            "sky_garden_storeys": gardens,
        })
    out = {
        "fixture_version": "dawson-v2",
        "generated_on": "2026-09-03",
        "coordinate_frame": v1["coordinate_frame"],
        "target": {"block": "87", "address": "87 Dawson Road", "postal_code": "141087", "storey_range": [2, 47], "demo_storey": 30},
        "height_basis": "3.6 m first storey + 2.8 m typical + 5.6 m sky-garden storeys (3/14/25/36) + 4.0 m roof structures; reconciles to 147.8 m published (assumed model)",
        "storey_model": {"first_m": FIRST_STOREY_M, "typical_m": TYPICAL_STOREY_M, "sky_garden_m": SKY_GARDEN_STOREY_M, "roof_m": ROOF_STRUCTURE_M, "state": "assumed"},
        "sources": v1["sources"] + [
            {"title": "HDB press release 3 Nov 2016 (sky gardens at storeys 3, 14, 25, 36)", "state": "verified_secondary"},
            {"title": "Architectural Record / Skyscraper Center tower height 147.8 m", "state": "verified_secondary"},
        ],
        "licence": "Singapore Open Data Licence v1.0 for footprints and storey counts; attribution required; no endorsement implied.",
        "buildings": buildings,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(OUT, hashlib.sha256(OUT.read_bytes()).hexdigest()[:16], len(buildings), "buildings")


if __name__ == "__main__":
    main()
