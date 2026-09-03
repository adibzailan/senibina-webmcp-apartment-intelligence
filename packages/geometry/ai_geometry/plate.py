"""Derive the Block 87 plate recipe (core + four wings + storey bands) from the sourced footprint.

The footprint comes from the HDB Existing Building dataset (sourced). Wings and core are
reconstructed by geometric decomposition (erosion), the slot split into one 4-room and one
3-room stack per wing is inferred from the Block 87 unit count (160 x 3R + 160 x 4R over
40 residential storeys = 4 + 4 per storey) and the WOHA storey-16-24 plan.
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .schema import PlateRecipe, Source, StoreyBand, Wing

# Storey-height model (assumed; reconciles to the published 147.8 m tower height):
FIRST_STOREY_M = 3.6
TYPICAL_STOREY_M = 2.8
SKY_GARDEN_STOREY_M = 5.6
ROOF_STRUCTURE_M = 4.0
SKY_GARDENS = [3, 14, 25, 36]
UNIT_4R_WIDTH_M = 12.51  # published 4R frontage (brochure p.5 scaled to 87 m2)
UNIT_3R_WIDTH_M = 9.2  # assumed; remaining wing length


def _rect_frame(g: Polygon):
    mrr = g.minimum_rotated_rectangle
    c = list(mrr.exterior.coords)[:4]
    e0 = math.dist(c[0], c[1])
    e1 = math.dist(c[1], c[2])
    if e0 >= e1:
        a, b, length, depth = c[0], c[1], e0, e1
        c_next = c[2]
    else:
        a, b, length, depth = c[1], c[2], e1, e0
        c_next = c[3]
    axis = math.atan2(b[1] - a[1], b[0] - a[0])
    return a, b, c_next, axis, length, depth


def wings_from_footprint(footprint: list[tuple[float, float]], erosion_m: float = 3.0):
    P = Polygon(footprint)
    E = P.buffer(-erosion_m)
    parts = sorted(getattr(E, "geoms", [E]), key=lambda g: -g.area)[:4]
    centre = P.centroid
    wings = []
    for g in parts:
        a, b, c_next, axis, length, depth = _rect_frame(g)
        length += 2 * erosion_m
        depth += 2 * erosion_m
        # the frontage is the long edge farthest from the plate centre
        mid_ab = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        mid_cd = (mid_ab[0] + (c_next[0] - b[0]), mid_ab[1] + (c_next[1] - b[1]))
        if math.dist(mid_ab, (centre.x, centre.y)) >= math.dist(mid_cd, (centre.x, centre.y)):
            front_mid, inward_vec = mid_ab, (mid_cd[0] - mid_ab[0], mid_cd[1] - mid_ab[1])
        else:
            front_mid, inward_vec = mid_cd, (mid_ab[0] - mid_cd[0], mid_ab[1] - mid_cd[1])
        inward = math.atan2(inward_vec[1], inward_vec[0])
        # push the frontage midpoint outward by the erosion so it sits on the true outer edge
        ux, uy = math.cos(inward), math.sin(inward)
        front_mid = (front_mid[0] - ux * erosion_m, front_mid[1] - uy * erosion_m)
        # make the x axis such that (x, y) is right-handed with y = inward
        axis_deg = math.degrees(inward) - 90.0
        wings.append(dict(front_mid=front_mid, axis_deg=axis_deg, inward_deg=math.degrees(inward), length=length, depth=depth, centroid=(g.centroid.x, g.centroid.y)))
    # name wings by compass quadrant of their centroid relative to the plate centre
    def quadrant(c):
        dx, dy = c[0] - centre.x, c[1] - centre.y
        return ("N" if dy >= 0 else "S") + ("E" if dx >= 0 else "W")
    for w in wings:
        w["id"] = quadrant(w["centroid"])
    wings.sort(key=lambda w: ["NE", "NW", "SW", "SE"].index(w["id"]))
    return wings


def core_from_footprint(footprint, erosion_m: float = 3.0):
    P = Polygon(footprint)
    E = P.buffer(-erosion_m)
    parts = sorted(getattr(E, "geoms", [E]), key=lambda g: -g.area)
    wings = unary_union([g.buffer(erosion_m + 0.05) for g in parts[:4]])
    core = P.difference(wings)
    core = max(getattr(core, "geoms", [core]), key=lambda g: g.area)
    return [(round(x, 3), round(y, 3)) for x, y in core.exterior.coords[:-1]]


def storey_bands(storeys: int, sky_gardens: list[int]) -> list[StoreyBand]:
    src = Source(state="assumed", document="HDB Precast Pictorial Guide 2014 (2.8 m typical, 3.6 m first); sky-garden storeys double height reconciles to 147.8 m published", confidence_m=1.5)
    bands = []
    z = 0.0
    s = 1
    while s <= storeys:
        if s == 1:
            kind, h, end = "podium", FIRST_STOREY_M, 1
        elif s in sky_gardens:
            kind, h, end = "sky_garden", SKY_GARDEN_STOREY_M, s
        else:
            kind, h = "typical", TYPICAL_STOREY_M
            end = s
            while end + 1 <= storeys and (end + 1) not in sky_gardens:
                end += 1
        n = end - s + 1
        bands.append(StoreyBand(id=f"s{s}-{end}", storeys=(s, end), kind=kind, storey_height_m=h, base_m=round(z, 3), top_m=round(z + n * h, 3), source=src))
        z += n * h
        s = end + 1
    bands.append(StoreyBand(id="roof", storeys=(storeys + 1, storeys + 1), kind="roof", storey_height_m=ROOF_STRUCTURE_M, base_m=round(z, 3), top_m=round(z + ROOF_STRUCTURE_M, 3), source=src))
    return bands


def storey_floor_level(bands: list[StoreyBand], storey: int) -> float:
    for b in bands:
        if b.storeys[0] <= storey <= b.storeys[1]:
            return round(b.base_m + (storey - b.storeys[0]) * b.storey_height_m, 3)
    raise ValueError(f"storey {storey} outside bands")


def build_block87_plate(building: dict, height_published_m: float = 147.8) -> PlateRecipe:
    fp = [tuple(p) for p in building["footprint"]]
    wings_raw = wings_from_footprint(fp)
    wsrc = Source(state="reconstructed", document="HDB Existing Building footprint decomposed; slot split inferred from 160x3R+160x4R and WOHA plan 16-24", confidence_m=0.5)
    wings = []
    for w in wings_raw:
        # slot layout along the wing: 4R at the wing tip ("end") is the default; both are assumed.
        slots = [
            {"id": "end", "unit_type": "4R", "start_m": 0.0, "width_m": UNIT_4R_WIDTH_M, "state": "assumed"},
            {"id": "inner", "unit_type": "4R", "start_m": round(w["length"] - UNIT_4R_WIDTH_M, 3), "width_m": UNIT_4R_WIDTH_M, "state": "assumed"},
        ]
        wings.append(Wing(id=w["id"], label=f"Wing {w['id']}", origin=(round(w["front_mid"][0], 3), round(w["front_mid"][1], 3)), axis_deg=round(w["axis_deg"], 3), inward_deg=round(w["inward_deg"], 3), length_m=round(w["length"], 3), depth_m=round(w["depth"], 3), slots=slots, source=wsrc))
    bands = storey_bands(building["max_floor_level"], SKY_GARDENS)
    return PlateRecipe(
        id="skyville-block87-plate",
        project="SkyVille @ Dawson",
        block=building["block"],
        address=building["address"],
        postal_code=building["postal_code"],
        footprint=[(round(x, 3), round(y, 3)) for x, y in fp],
        core=core_from_footprint(fp),
        wings=wings,
        bands=bands,
        storeys=building["max_floor_level"],
        height_published_m=height_published_m,
        sky_garden_storeys=SKY_GARDENS,
        overhang_depth_m=1.5,
        source=Source(state="inferred", document="HDB Existing Building d_16b157c52ed637edd6ba1232e026258d + HDB Property Information d_17f5382f26140b1fdae0ba2ef6239d2f + HDB press release 3 Nov 2016 (sky gardens 3/14/25/36)", confidence_m=0.5),
        limitations=[
            "Upper-storey plate is the ground footprint extruded; no storey-30 plan is published.",
            "Which wing end holds the 4-room stack is unknown; the resident chooses a slot and it is labelled assumed.",
            "Sky-garden storeys are modelled as core-only voids with a slab overhang of assumed depth.",
            "Storey heights are an assumed model (3.6 / 2.8 / 5.6 m) reconciled to the published 147.8 m.",
        ],
    )
