"""Gate 1 overlay: draw a recipe as SVG on top of a local raster (raster never committed).

Calibration: a raster pixel frame -> plan frame similarity (scale, rotation, translation)."""
from __future__ import annotations

import base64
import math
from pathlib import Path


def svg_overlay(image_path: Path, width_px: int, height_px: int, m_per_px: float, origin_px: tuple[float, float], polylines: list[tuple[str, list[tuple[float, float]], str]], flip_y: bool = False, title: str = "") -> str:
    """polylines: (id, points in plan metres, colour). origin_px = pixel of plan (0,0)."""
    data = base64.b64encode(Path(image_path).read_bytes()).decode()
    mime = "image/png" if str(image_path).lower().endswith(".png") else "image/jpeg"

    def tx(p):
        x = origin_px[0] + p[0] / m_per_px
        y = origin_px[1] + (-p[1] if flip_y else p[1]) / m_per_px
        return f"{x:.1f},{y:.1f}"

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}" viewBox="0 0 {width_px} {height_px}">', f"<title>{title}</title>", f'<image href="data:{mime};base64,{data}" width="{width_px}" height="{height_px}" opacity="0.85"/>']
    for pid, pts, colour in polylines:
        parts.append(f'<polyline id="{pid}" points="{" ".join(tx(p) for p in pts)}" fill="none" stroke="{colour}" stroke-width="2" stroke-opacity="0.9"/>')
    parts.append("</svg>")
    return "\n".join(parts)
