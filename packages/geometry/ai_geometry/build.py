"""Builders: recipe + placement -> element boxes (world ENU metres), visual + analytical meshes, sensors.

One geometry, two meshes: the visual scene keeps every element (with provenance and opacity
tokens); the analytical mesh keeps only `blocks_sun` elements and is watertight.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box as shp_box
from shapely.ops import unary_union

from .plate import storey_floor_level
from .schema import Element, PlateRecipe, UnitRecipe

OPACITY = {"context": 0.16, "tower": 0.28, "home": 1.0, "glass": 0.35}
FACADES = ("NE", "NW", "SW", "SE")


@dataclass
class Placement:
    storey: int
    facade: str = "NE"
    stack_position: str = "end"
    variant: str = "A"
    mirrored: bool = False
    openings: dict[str, bool] = field(default_factory=dict)

    def as_dict(self):
        return {"storey": self.storey, "facade": self.facade, "stack_position": self.stack_position, "variant": self.variant, "mirrored": self.mirrored, "openings": dict(sorted(self.openings.items()))}


@dataclass
class Frame2D:
    """Unit plan frame -> world ENU. x along frontage, y inward, origin at the frontage midpoint of the slot."""
    origin: tuple[float, float]
    axis_rad: float
    inward_rad: float
    mirrored: bool = False

    def to_world(self, x: float, y: float) -> tuple[float, float]:
        if self.mirrored:
            x = -x
        ax, ay = math.cos(self.axis_rad), math.sin(self.axis_rad)
        ix, iy = math.cos(self.inward_rad), math.sin(self.inward_rad)
        return (self.origin[0] + x * ax + y * ix, self.origin[1] + x * ay + y * iy)

    def poly_to_world(self, pts):
        return [self.to_world(x, y) for x, y in pts]


def unit_frame(plate: PlateRecipe, placement: Placement) -> Frame2D:
    wing = next((w for w in plate.wings if w.id == placement.facade), None)
    if wing is None:
        raise ValueError("PLACEMENT_INVALID: unknown facade")
    slot = next((s for s in wing.slots if s["id"] == placement.stack_position), None)
    if slot is None:
        raise ValueError("PLACEMENT_INVALID: unknown stack_position")
    axis = math.radians(wing.axis_deg)
    inward = math.radians(wing.inward_deg)
    centre_along = slot["start_m"] + slot["width_m"] / 2 - wing.length_m / 2
    ox = wing.origin[0] + centre_along * math.cos(axis)
    oy = wing.origin[1] + centre_along * math.sin(axis)
    return Frame2D(origin=(ox, oy), axis_rad=axis, inward_rad=inward, mirrored=placement.mirrored)


@dataclass
class Box:
    id: str
    kind: str
    polygon: list[tuple[float, float]]  # world XY outline (convex or simple)
    z0: float
    z1: float
    blocks_sun: bool
    opacity_token: str
    extras: dict

    def mesh(self) -> trimesh.Trimesh:
        return extrude_polygon(self.polygon, self.z0, self.z1)


def extrude_polygon(poly_xy, z0, z1) -> trimesh.Trimesh:
    """Extrude a simple polygon (holes supported) into a closed, outward-facing mesh.

    Uses ladybug-geometry's pure-Python earcut, so no extra triangulation dependency."""
    from ladybug_geometry.triangulation import earcut

    P = Polygon(poly_xy)
    if not P.is_valid or P.area <= 1e-9:
        P = P.buffer(0)
        if P.geom_type != "Polygon":
            P = max(P.geoms, key=lambda g: g.area)
    P = orient_polygon(P)
    rings = [list(P.exterior.coords[:-1])] + [list(h.coords[:-1]) for h in P.interiors]
    flat, hole_idx, n = [], [], 0
    for i, r in enumerate(rings):
        if i > 0:
            hole_idx.append(n)
        for x, y in r:
            flat += [x, y]
        n += len(r)
    tris = earcut(flat, hole_idx or None, 2)
    pts2 = [(flat[2 * i], flat[2 * i + 1]) for i in range(n)]
    verts = [(x, y, z0) for x, y in pts2] + [(x, y, z1) for x, y in pts2]
    faces = []
    for i in range(0, len(tris), 3):
        a, b, c = tris[i], tris[i + 1], tris[i + 2]
        faces.append((a, c, b))  # bottom faces down
        faces.append((a + n, b + n, c + n))  # top faces up
    for r_i, r in enumerate(rings):
        start = sum(len(x) for x in rings[:r_i])
        m = len(r)
        for k in range(m):
            i0 = start + k
            i1 = start + (k + 1) % m
            faces.append((i0, i1, i1 + n))
            faces.append((i0, i1 + n, i0 + n))
    mesh = trimesh.Trimesh(vertices=np.array(verts, dtype=np.float64), faces=np.array(faces, dtype=np.int64), process=False)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def orient_polygon(P: Polygon) -> Polygon:
    from shapely.geometry.polygon import orient

    return orient(P, sign=1.0)  # exterior CCW, holes CW


def _wall_segment_polygon(a, b, t):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return None
    nx, ny = -dy / L * t / 2, dx / L * t / 2
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def _point_along(a, b, s):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (a[0] + dx / L * s, a[1] + dy / L * s)


def wall_pieces(wall: Element, openings: list[Element], z_floor: float, frame: Frame2D):
    """Split a wall into solid boxes around its openings. Returns (solids, glazing)."""
    solids, glazing = [], []
    a, b = wall.polyline[0], wall.polyline[1]
    L = math.dist(a, b)
    ops = sorted([o for o in openings if o.host_wall == wall.id], key=lambda o: o.along_m[0])
    cursor = 0.0
    z0, z1 = z_floor + wall.base_m, z_floor + wall.base_m + wall.height_m
    idx = 0

    def piece(s0, s1, zz0, zz1, tag, blocks, token, extra):
        if s1 - s0 < 1e-3 or zz1 - zz0 < 1e-3:
            return None
        pa, pb = _point_along(a, b, s0), _point_along(a, b, s1)
        poly = _wall_segment_polygon(frame.to_world(*pa), frame.to_world(*pb), wall.thickness_m)
        return Box(id=tag, kind=wall.kind if blocks else "opening", polygon=poly, z0=zz0, z1=zz1, blocks_sun=blocks, opacity_token=token, extras=extra)

    wx = {"element": wall.id, "state": wall.source.state, "confidence_m": wall.source.confidence_m, "document": wall.source.document}
    for o in ops:
        s0, s1 = max(0.0, o.along_m[0]), min(L, o.along_m[1])
        p = piece(cursor, s0, z0, z1, f"{wall.id}#{idx}", True, wall.opacity_token, wx)
        if p:
            solids.append(p); idx += 1
        oz0, oz1 = z_floor + o.base_m, z_floor + o.base_m + o.height_m
        below = piece(s0, s1, z0, oz0, f"{wall.id}#{idx}", True, wall.opacity_token, wx)
        if below:
            solids.append(below); idx += 1
        above = piece(s0, s1, oz1, z1, f"{wall.id}#{idx}", True, wall.opacity_token, wx)
        if above:
            solids.append(above); idx += 1
        g = piece(s0, s1, oz0, oz1, o.id, False, "glass", {"element": o.id, "state": o.source.state, "confidence_m": o.source.confidence_m, "document": o.source.document})
        if g:
            glazing.append(g)
        cursor = s1
    p = piece(cursor, L, z0, z1, f"{wall.id}#{idx}", True, wall.opacity_token, wx)
    if p:
        solids.append(p)
    return solids, glazing


def unit_boxes(unit: UnitRecipe, plate: PlateRecipe, placement: Placement) -> list[Box]:
    frame = unit_frame(plate, placement)
    z = storey_floor_level(plate.bands, placement.storey)
    enabled = {e.id: placement.openings.get(e.id, e.enabled_by_default) for e in unit.elements}
    openings = [e for e in unit.elements if e.kind == "opening" and enabled[e.id]]
    out: list[Box] = []
    for e in unit.elements:
        if not enabled[e.id]:
            continue
        ex = {"element": e.id, "kind": e.kind, "state": e.source.state, "confidence_m": e.source.confidence_m, "document": e.source.document}
        if e.kind == "opening":
            continue
        if e.kind == "wall":
            s, g = wall_pieces(e, openings, z, frame)
            out += s + g
        elif e.kind == "railing":
            poly = _wall_segment_polygon(frame.to_world(*e.polyline[0]), frame.to_world(*e.polyline[1]), e.thickness_m)
            out.append(Box(e.id, e.kind, poly, z + e.base_m, z + e.base_m + e.height_m, e.blocks_sun, e.opacity_token, ex))
        else:
            if e.rect is not None:
                x0, y0, x1, y1 = e.rect
                pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            else:
                pts = e.polyline
            out.append(Box(e.id, e.kind, frame.poly_to_world(pts), z + e.base_m, z + e.base_m + e.height_m, e.blocks_sun, e.opacity_token, ex))
    return out


def plate_boxes(plate: PlateRecipe, unit: UnitRecipe, placement: Placement) -> list[Box]:
    """Target tower per band: extruded footprint; sky-garden storeys core-only plus slab overhang;
    home storey = footprint minus the unit envelope."""
    frame = unit_frame(plate, placement)
    env = Polygon(frame.poly_to_world(unit.envelope))
    fp = Polygon(plate.footprint)
    core = Polygon(plate.core)
    src = {"element": "plate", "state": "inferred", "confidence_m": plate.source.confidence_m, "document": plate.source.document}
    out = []
    for b in plate.bands:
        if b.kind == "sky_garden":
            out.append(Box(f"core-{b.id}", "core", list(core.exterior.coords[:-1]), b.base_m, b.top_m, True, "tower", {**src, "element": "core"}))
            oh = fp.buffer(plate.overhang_depth_m, join_style=2)
            out.append(Box(f"overhang-{b.id}", "overhang", list(oh.exterior.coords[:-1]), b.top_m - 0.3, b.top_m, True, "tower", {**src, "element": "sky-garden-slab", "state": "assumed"}))
            continue
        if b.kind == "roof":
            out.append(Box(f"roof-{b.id}", "core", list(core.exterior.coords[:-1]), b.base_m, b.top_m, True, "tower", {**src, "element": "roof-structure", "state": "assumed"}))
            continue
        s0, s1 = b.storeys
        if s0 <= placement.storey <= s1:
            zf = storey_floor_level(plate.bands, placement.storey)
            if placement.storey > s0:
                out.append(Box(f"plate-{b.id}-below", "slab", list(fp.exterior.coords[:-1]), b.base_m, zf, True, "tower", src))
            rest = fp.difference(env.buffer(0.01))
            for i, g in enumerate(getattr(rest, "geoms", [rest])):
                if g.area > 0.5:
                    out.append(Box(f"plate-{b.id}-home-{i}", "slab", list(g.exterior.coords[:-1]), zf - 0.2, zf + b.storey_height_m, True, "tower", {**src, "element": "plate-home-storey"}))
            if placement.storey < s1:
                out.append(Box(f"plate-{b.id}-above", "slab", list(fp.exterior.coords[:-1]), zf + b.storey_height_m, b.top_m, True, "tower", src))
        else:
            out.append(Box(f"plate-{b.id}", "slab", list(fp.exterior.coords[:-1]), b.base_m, b.top_m, True, "tower", src))
    return out


def neighbour_boxes(precinct: dict, target_block: str) -> list[Box]:
    out = []
    for bld in precinct["buildings"]:
        if bld["block"] == target_block:
            continue
        out.append(Box(bld["id"], "slab", [tuple(p) for p in bld["footprint"]], 0.0, bld["height_m"], True, "context", {"element": bld["id"], "address": bld["address"], "state": bld.get("height_state", "inferred"), "confidence_m": 1.5, "document": "HDB Existing Building + Property Information (extruded)"}))
    return out


@dataclass
class Scene:
    boxes: list[Box]
    placement: Placement

    def analytical_mesh(self) -> trimesh.Trimesh:
        parts = [b.mesh() for b in self.boxes if b.blocks_sun]
        m = trimesh.util.concatenate(parts)
        return m

    def visual_scene(self) -> trimesh.Scene:
        sc = trimesh.Scene()
        for b in sorted(self.boxes, key=lambda b: b.id):
            m = b.mesh()
            a = int(round(OPACITY[b.opacity_token] * 255))
            rgb = {"context": (150, 150, 150), "tower": (120, 130, 150), "home": (240, 236, 228), "glass": (140, 190, 230)}[b.opacity_token]
            m.visual = trimesh.visual.ColorVisuals(m, face_colors=[rgb + (a,)] * len(m.faces))
            sc.add_geometry(m, node_name=b.id, geom_name=b.id, metadata={**b.extras, "opacity_token": b.opacity_token, "opacity": OPACITY[b.opacity_token], "blocks_sun": b.blocks_sun, "kind": b.kind})
        return sc


def build_scene(precinct: dict, plate: PlateRecipe, unit: UnitRecipe, placement: Placement) -> Scene:
    boxes = neighbour_boxes(precinct, plate.block) + plate_boxes(plate, unit, placement) + unit_boxes(unit, plate, placement)
    return Scene(boxes=boxes, placement=placement)


def sensor_grid(unit: UnitRecipe, plate: PlateRecipe, placement: Placement, spacing_m: float = 0.25, offset_m: float = 0.8):
    """Floor sensors on a regular plan grid inside rooms, excluding walls/columns/shelter. Returns dict."""
    frame = unit_frame(plate, placement)
    z = storey_floor_level(plate.bands, placement.storey) + offset_m
    enabled = {e.id: placement.openings.get(e.id, e.enabled_by_default) for e in unit.elements}
    solids = []
    for e in unit.elements:
        if not enabled[e.id] or e.kind not in ("wall", "column"):
            continue
        if e.kind == "wall":
            solids.append(Polygon(_wall_segment_polygon(e.polyline[0], e.polyline[1], e.thickness_m)))
        else:
            solids.append(shp_box(*e.rect))
    blocked = unary_union(solids)
    rooms = {r.id: Polygon(r.polygon) for r in unit.rooms if r.id not in ("shelter", "ac_ledge")}
    xs = [p[0] for p in unit.envelope]; ys = [p[1] for p in unit.envelope]
    nx = int(math.floor((max(xs) - min(xs)) / spacing_m)); ny = int(math.floor((max(ys) - min(ys)) / spacing_m))
    x_start = min(xs) + ((max(xs) - min(xs)) - nx * spacing_m) / 2 + spacing_m / 2
    y_start = min(ys) + ((max(ys) - min(ys)) - ny * spacing_m) / 2 + spacing_m / 2
    pts, room_ids, cols, rows, local = [], [], [], [], []
    for j in range(ny):
        for i in range(nx):
            x, y = x_start + i * spacing_m, y_start + j * spacing_m
            p = Point(x, y)
            rid = next((r for r, g in rooms.items() if g.contains(p)), None)
            if rid is None or blocked.contains(p):
                continue
            wx, wy = frame.to_world(x, y)
            pts.append((round(wx, 4), round(wy, 4), round(z, 4)))
            room_ids.append(rid); cols.append(i); rows.append(j); local.append((round(x, 4), round(y, 4)))
    return {"grid": {"columns": nx, "rows": ny, "spacing_m": spacing_m, "offset_m": offset_m, "x_start": round(x_start, 4), "y_start": round(y_start, 4)}, "xyz": pts, "local_xy": local, "room_ids": room_ids, "col": cols, "row": rows, "count": len(pts)}
