"""Gate 1: render recipe overlays on the local rasters (never committed). Output: output/gate1/*.svg + png.

Usage: .venv/bin/python tests/acceptance/gate1_overlays.py [--unit-scale M_PER_PX --unit-origin X,Y --plate-scale --plate-origin --plate-rot]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image

from ai_geometry.overlay import svg_overlay
from ai_geometry.schema import PlateRecipe, UnitRecipe
from ai_geometry.build import unit_frame, Placement

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "output/research/skyville-dawson-floorplans-2026-09-02"
OUT = ROOT / "output/gate1"


def png_overlay(img_path, m_per_px, origin_px, lines, flip_y, out):
    from PIL import ImageDraw
    im = Image.open(img_path).convert("RGB")
    dr = ImageDraw.Draw(im)
    for pid, pts, colour in lines:
        xy = [(origin_px[0] + p[0] / m_per_px, origin_px[1] + (-p[1] if flip_y else p[1]) / m_per_px) for p in pts]
        if len(xy) >= 2:
            dr.line(xy, fill=colour, width=3)
    im.save(out)


def unit_overlay(variant: str, crop_box, m_per_px: float, origin_px, scratch_img: Path):
    page = Image.open(RES / "bto-brochure-pages/page-5.png")
    crop = page.crop(crop_box).resize((1410, 1080), Image.LANCZOS)
    crop.save(scratch_img)
    u = UnitRecipe.model_validate(json.loads((ROOT / f"data/recipes/4r-type-{variant}.recipe.json").read_text()))
    lines = [("envelope", u.envelope + [u.envelope[0]], "#e00")]
    for e in u.elements:
        if e.kind == "wall":
            lines.append((e.id, e.polyline, "#06c"))
        elif e.kind == "column":
            x0, y0, x1, y1 = e.rect; lines.append((e.id, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], "#080"))
        elif e.kind in ("balcony", "ledge") and e.rect:
            x0, y0, x1, y1 = e.rect; lines.append((e.id, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], "#c60"))
        elif e.kind == "opening" and e.enabled_by_default:
            host = next(w for w in u.elements if w.id == e.host_wall)
            a, b = host.polyline[0], host.polyline[1]
            L = math.dist(a, b); s0, s1 = e.along_m
            p = lambda s: (a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L)
            lines.append((e.id, [p(s0), p(s1)], "#fa0" if e.base_m > 0 else "#a0f"))
    svg = svg_overlay(scratch_img, 1410, 1080, m_per_px, origin_px, lines, title=f"4R Type {variant.upper()} recipe over brochure p.5")
    (OUT / f"unit-4r-type-{variant}.svg").write_text(svg)
    png_overlay(scratch_img, m_per_px, origin_px, lines, False, OUT / f"unit-4r-type-{variant}.png")


def plate_overlay(px_per_m: float, centre_px, rot_deg: float, crop_box, scratch_img: Path):
    img = Image.open(RES / "architectural-plans/05-storey-plan.jpg").crop(crop_box)
    W, H = img.size
    img.save(scratch_img)
    p = PlateRecipe.model_validate(json.loads((ROOT / "data/recipes/skyville-block87-plate.recipe.json").read_text()))
    r = math.radians(rot_deg)

    def rot(pt):
        x, y = pt
        return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r))
    lines = [("footprint", [rot(q) for q in p.footprint + [p.footprint[0]]], "#e00"), ("core", [rot(q) for q in p.core + [p.core[0]]], "#080")]
    for w in p.wings:
        ax = math.radians(w.axis_deg); inw = math.radians(w.inward_deg)
        o = w.origin
        for s in w.slots:
            c0 = s["start_m"] - w.length_m / 2; c1 = c0 + s["width_m"]
            def P(c, d): return rot((o[0] + c * math.cos(ax) + d * math.cos(inw), o[1] + c * math.sin(ax) + d * math.sin(inw)))
            lines.append((f"{w.id}-{s['id']}", [P(c0, 0), P(c1, 0), P(c1, w.depth_m), P(c0, w.depth_m), P(c0, 0)], "#06c" if s["id"] == "end" else "#c60"))
    u = UnitRecipe.model_validate(json.loads((ROOT / "data/recipes/4r-type-a.recipe.json").read_text()))
    f = unit_frame(p, Placement(storey=30, facade="NE", stack_position="end"))
    lines.append(("unit-NE-end", [rot(q) for q in f.poly_to_world(u.envelope + [u.envelope[0]])], "#a0f"))
    svg = svg_overlay(scratch_img, W, H, 1 / px_per_m, centre_px, lines, flip_y=True, title="Block 87 plate recipe over WOHA storey-5 plan (calibrated by eye; sourced footprint in red)")
    (OUT / "plate-block87-over-storey5.svg").write_text(svg)
    png_overlay(scratch_img, 1 / px_per_m, centre_px, lines, True, OUT / "plate-block87-over-storey5.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit-scale", type=float, default=12.51 / 1225)
    ap.add_argument("--unit-origin", default="700,150")
    ap.add_argument("--plate-scale", type=float, default=9.8)
    ap.add_argument("--plate-centre", default="380,195")
    ap.add_argument("--plate-rot", type=float, default=13.0)
    ap.add_argument("--scratch", default=str(OUT))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    uo = tuple(float(v) for v in a.unit_origin.split(","))
    for v, box in (("a", (430, 290, 900, 650)), ("b", (430, 660, 900, 1020)), ("c", (430, 1030, 900, 1390))):
        unit_overlay(v, box, a.unit_scale, uo, Path(a.scratch) / f"_crop-{v}.png")
    pc = tuple(float(v) for v in a.plate_centre.split(","))
    plate_overlay(a.plate_scale, pc, a.plate_rot, (500, 0, 1200, 560), Path(a.scratch) / "_crop-plate.png")
    print("wrote", sorted(x.name for x in OUT.glob("*.svg")))
