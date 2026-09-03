"""4-room Type A/B/C recipes traced from the HDB SkyVille @ Dawson brochure (Dec 2009, p.5).

Frame: x runs along the window frontage (metres, centred), y runs from the frontage (y=0)
into the unit. Coordinates were read from the brochure raster with the published 12.5 m
frontage as the scale (0.0102 m/px on the 1410 px upscaled crop). Tolerance +-0.2-0.3 m.
Only coordinates are stored; the raster is never committed.
"""
from __future__ import annotations

from .schema import Element, Room, Source, UnitRecipe

BROCHURE = "HDB SkyVille @ Dawson BTO Dec 2009 sales brochure, Flexi-Layout Scheme, 4R Type A/B/C"
PUB = Source(state="published", document=BROCHURE, page=5, calibration_id="cal-4r-brochure-p5", confidence_m=0.25)
REC = Source(state="reconstructed", document=BROCHURE, page=5, calibration_id="cal-4r-brochure-p5", confidence_m=0.3)
ASSUMED = Source(state="assumed", document="typical HDB detailing; not on the published plan", confidence_m=0.5)

HALF = 6.255
EXT = 0.2
INT = 0.1
SHELTER = 0.3
WALL_H = 2.6  # storey 2.8 minus 0.2 slab
SILL, HEAD = 1.0, 2.4

ENVELOPE = [(-HALF, 0.0), (HALF, 0.0), (HALF, 6.05), (5.65, 6.05), (5.65, 6.95), (3.72, 6.95), (3.72, 8.78), (-1.81, 8.78), (-1.81, 6.33), (-HALF, 6.33)]


def _wall(id_, pts, t=INT, src=REC, **kw):
    return Element(id=id_, kind="wall", polyline=pts, thickness_m=t, height_m=WALL_H, source=src, **kw)


def _col(id_, cx, cy, s=0.5, src=REC):
    return Element(id=id_, kind="column", rect=(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2), height_m=WALL_H, source=src)


def _win(id_, host, a, b, src=PUB, enabled=True):
    return Element(id=id_, kind="opening", host_wall=host, along_m=(a, b), base_m=SILL, height_m=HEAD - SILL, blocks_sun=False, opacity_token="glass", source=src, enabled_by_default=enabled)


def _door(id_, host, a, b):
    return Element(id=id_, kind="opening", host_wall=host, along_m=(a, b), base_m=0.0, height_m=2.1, blocks_sun=False, opacity_token="glass", source=REC)


def exterior_walls():
    els = []
    n = len(ENVELOPE)
    for i in range(n):
        a, b = ENVELOPE[i], ENVELOPE[(i + 1) % n]
        els.append(_wall(f"ext-{i}", [a, b], t=EXT, src=PUB if i == 0 else REC))
    return els


def common_interior(variant: str):
    """Walls shared by all variants (wet zone, kitchen, shelter)."""
    w = [
        _wall("w-corridor-south", [(-5.18, 4.49), (0.44, 4.49)]),
        _wall("w-acledge-east", [(-4.26, 4.49), (-4.26, 6.33)]),
        _wall("w-bath1-east", [(-2.12, 4.49), (-2.12, 6.33)]),
        _wall("w-shaft-east", [(-1.51, 4.49), (-1.51, 6.33)]),
        _wall("w-bath2-east", [(0.13, 4.49), (0.13, 6.33)]),
        _wall("w-shelter-west", [(0.44, 4.49), (0.44, 6.33)], t=SHELTER),
        _wall("w-shelter-north", [(0.44, 4.49), (2.78, 4.49)], t=SHELTER),
        _wall("w-shelter-east", [(2.78, 4.49), (2.78, 6.33)], t=SHELTER),
        _wall("w-shelter-south", [(0.44, 6.33), (2.78, 6.33)], t=SHELTER),
        _wall("w-wet-south", [(-4.26, 6.33), (0.44, 6.33)]),
        _wall("w-living-south", [(2.78, 6.33), (3.72, 6.33)]),
        _wall("w-serviceyard-east", [(0.74, 6.33), (0.74, 8.78)]),
        _wall("w-kitchen-corridor", [(3.72, 6.33), (3.72, 6.95)]),
    ]
    return w


def bedroom_walls(variant: str):
    a = [
        _wall("w-mainbed-east", [(-2.93, 0.0), (-2.93, 4.39)]),
        _wall("w-mainbed-south", [(-HALF, 4.39), (-2.93, 4.39)]),
        _wall("w-bed2-east", [(0.03, 0.0), (0.03, 3.47)]),
        _wall("w-bed2-south", [(-2.93, 3.47), (0.03, 3.47)]),
        _wall("w-bed3-east", [(2.78, 0.0), (2.78, 3.47)]),
        _wall("w-bed3-south", [(0.03, 3.47), (2.78, 3.47)]),
    ]
    if variant == "A":
        return a
    if variant == "B":  # bedroom 3 removed into the living room
        return [w for w in a if not w.id.startswith("w-bed3")]
    if variant == "C":  # master suite absorbs bedroom 2; bedroom 3 removed
        keep = {"w-mainbed-south", "w-bed2-east", "w-bed2-south"}
        out = [w for w in a if w.id in keep]
        out[0] = _wall("w-mainbed-south", [(-HALF, 4.39), (-2.93, 4.39)])
        return out
    raise ValueError(variant)


def openings(variant: str):
    o = [
        _win("win-mainbed", "ext-0", 1.28, 2.70),
        _win("win-bed2", "ext-0", 4.03, 5.46),
        _win("win-bed3", "ext-0", 7.09, 8.42),
        _win("win-living", "ext-0", 9.85, 11.79),
        _win("win-living-side", "ext-1", 0.5, 4.1, src=ASSUMED),
        _win("win-mainbed-side", "ext-9", 2.1, 5.6, src=ASSUMED, enabled=False),
        _win("win-kitchen", "ext-6", 0.5, 2.6, src=ASSUMED),
        _door("door-entrance", "ext-3", 0.1, 1.0),
        _door("door-mainbed", "w-mainbed-east", 3.3, 4.2),
        _door("door-bed2", "w-bed2-south", 1.9, 2.8),
        _door("door-bed3", "w-bed3-south", 0.2, 1.1),
        _door("door-bath1", "w-corridor-south", 1.2, 2.0),
        _door("door-bath2", "w-corridor-south", 3.9, 4.7),
        _door("door-shelter", "w-shelter-north", 0.5, 1.3),
        _door("door-kitchen", "w-kitchen-corridor", 0.05, 0.6),
    ]
    if variant in ("B", "C"):
        o = [x for x in o if x.id != "door-bed3"]
    if variant == "C":
        o = [x for x in o if x.id not in ("door-bed2", "door-mainbed")]
        o.append(_door("door-master", "w-bed2-south", 1.9, 2.8))
    return o


def columns():
    cs = []
    for i, cx in enumerate([-5.4, -2.85, -0.4, 2.25, 5.55]):
        cs.append(_col(f"col-front-{i}", cx, -0.1))
    for i, (cx, cy) in enumerate([(-1.81, 8.78), (3.72, 8.78), (-HALF, 6.33), (HALF, 6.05)]):
        cs.append(_col(f"col-rear-{i}", cx, cy, s=0.45))
    return cs


def slabs_and_extras():
    return [
        Element(id="slab-floor", kind="slab", polyline=ENVELOPE, base_m=-0.2, height_m=0.2, opacity_token="home", source=REC),
        Element(id="slab-ceiling", kind="slab", polyline=ENVELOPE, base_m=WALL_H, height_m=0.2, opacity_token="home", source=REC),
        Element(id="ledge-ac", kind="ledge", rect=(-5.18, 4.49, -4.26, 6.33), base_m=0.0, height_m=0.1, blocks_sun=False, opacity_token="home", source=REC, room="ac_ledge"),
        Element(id="railing-serviceyard", kind="railing", polyline=[(-1.81, 8.78), (0.74, 8.78)], thickness_m=0.05, base_m=0.0, height_m=1.0, blocks_sun=False, opacity_token="glass", source=ASSUMED),
        Element(id="balcony-living", kind="balcony", rect=(3.4, -1.3, 5.9, 0.0), base_m=-0.15, height_m=0.15, blocks_sun=True, opacity_token="home", source=ASSUMED, enabled_by_default=True),
        Element(id="railing-balcony", kind="railing", polyline=[(3.4, -1.3), (5.9, -1.3)], thickness_m=0.05, base_m=0.0, height_m=1.0, blocks_sun=False, opacity_token="glass", source=ASSUMED, enabled_by_default=True),
    ]


def rooms(variant: str):
    base = [
        Room(id="corridor", label="Corridor", polygon=[(-2.93, 3.47), (2.78, 3.47), (2.78, 4.49), (-2.93, 4.49)]),
        Room(id="ac_ledge", label="AC ledge", polygon=[(-5.18, 4.49), (-4.26, 4.49), (-4.26, 6.33), (-5.18, 6.33)]),
        Room(id="bath_1", label="Bath / WC 1", polygon=[(-4.26, 4.49), (-2.12, 4.49), (-2.12, 6.33), (-4.26, 6.33)]),
        Room(id="bath_2", label="Bath / WC 2", polygon=[(-1.51, 4.49), (0.13, 4.49), (0.13, 6.33), (-1.51, 6.33)]),
        Room(id="shelter", label="Household shelter", polygon=[(0.44, 4.49), (2.78, 4.49), (2.78, 6.33), (0.44, 6.33)]),
        Room(id="service_yard", label="Service yard", polygon=[(-1.81, 6.33), (0.74, 6.33), (0.74, 8.78), (-1.81, 8.78)]),
        Room(id="kitchen", label="Kitchen", polygon=[(0.74, 6.33), (3.72, 6.33), (3.72, 8.78), (0.74, 8.78)]),
        Room(id="entrance", label="Entrance", polygon=[(3.72, 6.33), (5.65, 6.33), (5.65, 6.95), (3.72, 6.95)]),
    ]
    if variant == "A":
        base += [
            Room(id="main_bedroom", label="Main bedroom", polygon=[(-HALF, 0.0), (-2.93, 0.0), (-2.93, 4.39), (-HALF, 4.39)]),
            Room(id="bedroom_2", label="Bedroom 2", polygon=[(-2.93, 0.0), (0.03, 0.0), (0.03, 3.47), (-2.93, 3.47)]),
            Room(id="bedroom_3", label="Bedroom 3", polygon=[(0.03, 0.0), (2.78, 0.0), (2.78, 3.47), (0.03, 3.47)]),
            Room(id="living_dining", label="Living / dining", polygon=[(2.78, 0.0), (HALF, 0.0), (HALF, 6.05), (5.65, 6.05), (5.65, 6.33), (2.78, 6.33)]),
        ]
    elif variant == "B":
        base += [
            Room(id="main_bedroom", label="Main bedroom", polygon=[(-HALF, 0.0), (-2.93, 0.0), (-2.93, 4.39), (-HALF, 4.39)]),
            Room(id="bedroom_2", label="Bedroom 2", polygon=[(-2.93, 0.0), (0.03, 0.0), (0.03, 3.47), (-2.93, 3.47)]),
            Room(id="living_dining", label="Living / dining", polygon=[(0.03, 0.0), (HALF, 0.0), (HALF, 6.05), (5.65, 6.05), (5.65, 6.33), (2.78, 6.33), (2.78, 3.47), (0.03, 3.47)]),
        ]
    else:
        base += [
            Room(id="main_bedroom", label="Master suite", polygon=[(-HALF, 0.0), (0.03, 0.0), (0.03, 3.47), (-2.93, 3.47), (-2.93, 4.39), (-HALF, 4.39)]),
            Room(id="living_dining", label="Living / dining", polygon=[(0.03, 0.0), (HALF, 0.0), (HALF, 6.05), (5.65, 6.05), (5.65, 6.33), (2.78, 6.33), (2.78, 3.47), (0.03, 3.47)]),
        ]
    return base


LABELS = {"A": "4R Type A - Base option (3 bedrooms)", "B": "4R Type B - Larger living room (2 bedrooms)", "C": "4R Type C - Master suite / larger living room"}


def build_4r(variant: str) -> UnitRecipe:
    variant = variant.upper()
    elements = exterior_walls() + common_interior(variant) + bedroom_walls(variant) + columns() + openings(variant) + slabs_and_extras()
    return UnitRecipe(
        id=f"skyville-4r-type-{variant.lower()}",
        project="SkyVille @ Dawson",
        unit_type="4R",
        variant=variant,
        label=LABELS[variant],
        frame_note="x along frontage (metres, centred), y from frontage into the unit; z up from finished floor",
        envelope=ENVELOPE,
        elements=elements,
        rooms=rooms(variant),
        source=PUB,
        limitations=[
            "Published typical 4-room plan; not a verified plan for any particular Block 87 dwelling or for storey 30.",
            "Window sill 1.0 m and head 2.4 m, side windows, kitchen window, balcony and railings are assumed.",
            "Wall positions carry +-0.25 m tolerance from raster tracing.",
        ],
    )
