#!/usr/bin/env python3
"""Build the frozen Dawson fixture from official data.gov.sg downloads."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import tempfile
import urllib.request
from datetime import date
from pathlib import Path


BUILDINGS_ID = "d_16b157c52ed637edd6ba1232e026258d"
PROPERTY_ID = "d_17f5382f26140b1fdae0ba2ef6239d2f"
API = "https://api-open.data.gov.sg/v1/public/api/datasets/{}/poll-download"
TARGET_POSTAL = "141087"
OUTPUT = Path(__file__).parents[1] / "fixtures" / "dawson-v1.json"


def fetch(dataset_id: str) -> tuple[bytes, str]:
    request = urllib.request.Request(API.format(dataset_id), headers={"User-Agent": "ApartmentIntelligence/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        url = json.load(response)["data"]["url"]
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    return payload, hashlib.sha256(payload).hexdigest()


def exterior(feature: dict) -> list[list[float]]:
    geometry = feature["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return max((polygon[0] for polygon in polygons), key=len)


def centroid(ring: list[list[float]]) -> tuple[float, float]:
    points = ring[:-1] if ring and ring[0] == ring[-1] else ring
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat = math.radians((a[1] + b[1]) / 2)
    return math.hypot(math.radians(a[0] - b[0]) * 6_371_000 * math.cos(lat), math.radians(a[1] - b[1]) * 6_371_000)


def enu(point: list[float], origin: tuple[float, float]) -> list[float]:
    lon, lat = map(math.radians, point[:2])
    lon0, lat0 = map(math.radians, origin)
    return [round((lon - lon0) * 6_371_000 * math.cos(lat0), 3), round((lat - lat0) * 6_371_000, 3)]


def main() -> None:
    buildings_bytes, buildings_hash = fetch(BUILDINGS_ID)
    property_bytes, property_hash = fetch(PROPERTY_ID)
    source = json.loads(buildings_bytes)
    properties = list(csv.DictReader(io.StringIO(property_bytes.decode("utf-8-sig"))))
    property_by_block = {
        row["blk_no"].strip(): row
        for row in properties
        if row["street"].strip().upper() == "DAWSON RD"
    }

    target = next(f for f in source["features"] if str(f["properties"].get("POSTAL_COD", "")).strip() == TARGET_POSTAL)
    origin = centroid(exterior(target))
    selected = []
    for feature in source["features"]:
        props = feature["properties"]
        ring = exterior(feature)
        centre = centroid(ring)
        if distance_m(centre, origin) > 350:
            continue
        row = property_by_block.get(str(props.get("BLK_NO", "")).strip())
        if not row:
            continue
        block = row["blk_no"].strip()
        digits = "".join(c for c in block if c.isdigit())
        if not digits or not 86 <= int(digits) <= 94:
            continue
        max_floor = int(row["max_floor_lvl"])
        selected.append({
            "id": f"hdb-{props['POSTAL_COD']}",
            "block": block,
            "address": f"{block} Dawson Road",
            "postal_code": str(props["POSTAL_COD"]),
            "max_floor_level": max_floor,
            "height_m": max_floor * 3.0,
            "height_state": "inferred",
            "footprint_state": "sourced",
            "footprint": [enu(point, origin) for point in ring],
        })

    fixture = {
        "fixture_version": "dawson-v1",
        "generated_on": date.today().isoformat(),
        "coordinate_frame": {"type": "local_enu_m", "origin_wgs84": [origin[0], origin[1]], "north": [0, 1, 0]},
        "target_postal_code": TARGET_POSTAL,
        "height_basis": "max_floor_level × 3.0 m",
        "sources": [
            {"dataset_id": BUILDINGS_ID, "url": f"https://data.gov.sg/datasets/{BUILDINGS_ID}/view", "sha256": buildings_hash},
            {"dataset_id": PROPERTY_ID, "url": f"https://data.gov.sg/datasets/{PROPERTY_ID}/view", "sha256": property_hash},
        ],
        "buildings": sorted(selected, key=lambda b: (int("".join(c for c in b["block"] if c.isdigit())), b["block"])),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT} with {len(selected)} buildings")


if __name__ == "__main__":
    main()
