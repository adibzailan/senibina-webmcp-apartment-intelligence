"""Byte-deterministic SVG evidence cards (no timestamps, fixed number formatting)."""
from __future__ import annotations

import math


def _f(v, nd=2):
    return f"{v:.{nd}f}"


def colour_ramp(t: float) -> str:
    """Ladybug-like ramp: blue -> cyan -> green -> yellow -> red."""
    stops = [(0.0, (0, 0, 180)), (0.25, (0, 170, 220)), (0.5, (0, 190, 90)), (0.75, (240, 220, 0)), (1.0, (210, 0, 0))]
    t = max(0.0, min(1.0, t))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= t <= b:
            u = (t - a) / (b - a)
            return "#%02x%02x%02x" % tuple(int(round(ca[i] + (cb[i] - ca[i]) * u)) for i in range(3))
    return "#000000"


def heatmap_card(result: dict, unit_envelope, key: str = "radiation", title: str = "Annual incident radiation, sensor plane 0.8 m", unit_label: str = "kWh/m² per year", values=None, north=None) -> str:
    s = result["sensors"]
    vals = values if values is not None else result["radiation"]["sensor_kwh_m2"]
    sp = s["grid"]["spacing_m"]
    xs = [p[0] for p in unit_envelope]; ys = [p[1] for p in unit_envelope]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    scale = 40.0  # px per metre
    W = int((maxx - minx) * scale) + 160; H = int((maxy - miny) * scale) + 140
    vmax = max(vals) if vals and max(vals) > 0 else 1.0
    vmin = min(vals) if vals else 0.0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>', f'<text x="20" y="28" font-size="16" fill="#111">{title}</text>',
           f'<text x="20" y="46" font-size="11" fill="#555">method {result["method_version"]} · digest {result["digest"][:16]} · {unit_label}</text>']
    ox, oy = 20.0, 60.0
    for (lx, ly), v in zip(s["local_xy"], vals):
        px = ox + (lx - minx - sp / 2) * scale; py = oy + (ly - miny - sp / 2) * scale
        out.append(f'<rect x="{_f(px)}" y="{_f(py)}" width="{_f(sp * scale)}" height="{_f(sp * scale)}" fill="{colour_ramp((v - vmin) / (vmax - vmin) if vmax > vmin else 0)}"/>')
    pts = " ".join(f"{_f(ox + (x - minx) * scale)},{_f(oy + (y - miny) * scale)}" for x, y in unit_envelope)
    out.append(f'<polygon points="{pts}" fill="none" stroke="#111" stroke-width="1.5"/>')
    lx = W - 120
    for i in range(20):
        out.append(f'<rect x="{lx}" y="{_f(oy + i * 8)}" width="18" height="8" fill="{colour_ramp(1 - i / 19)}"/>')
    out.append(f'<text x="{lx + 24}" y="{_f(oy + 8)}" font-size="11" fill="#111">{_f(vmax, 1)}</text>')
    out.append(f'<text x="{lx + 24}" y="{_f(oy + 160)}" font-size="11" fill="#111">{_f(vmin, 1)}</text>')
    if north is not None:
        out.append(north_arrow(W - 50, H - 60, north))
    out.append(f'<text x="20" y="{H - 16}" font-size="10" fill="#555">Computed evidence; upper-storey plate inferred, openings assumed. Not a daylight certification.</text>')
    out.append("</svg>")
    return "\n".join(out)


def north_arrow(cx: float, cy: float, north) -> str:
    """North arrow at (cx, cy). `north` is the unit vector toward true north in the card's plan frame (x right, y down)."""
    nx, ny = north
    L = 26.0
    tx, ty = cx + nx * L, cy + ny * L          # tip
    bx, by = cx - nx * L * 0.55, cy - ny * L * 0.55  # tail
    px, py = -ny, nx                            # perpendicular
    head = f"{_f(tx)},{_f(ty)} {_f(tx - nx * 10 + px * 5)},{_f(ty - ny * 10 + py * 5)} {_f(tx - nx * 10 - px * 5)},{_f(ty - ny * 10 - py * 5)}"
    lx, ly = cx + nx * (L + 12), cy + ny * (L + 12)
    return (f'<g><circle cx="{_f(cx)}" cy="{_f(cy)}" r="30" fill="none" stroke="#b9b7ae"/>'
            f'<line x1="{_f(bx)}" y1="{_f(by)}" x2="{_f(tx)}" y2="{_f(ty)}" stroke="#c8472d" stroke-width="2"/>'
            f'<polygon points="{head}" fill="#c8472d"/>'
            f'<text x="{_f(lx)}" y="{_f(ly + 4)}" font-size="11" text-anchor="middle" fill="#111">N</text></g>')


def sunpath_card(result: dict) -> str:
    W = H = 520; cx = cy = 260; R = 220
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">', f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="16" y="24" font-size="15" fill="#111">Sun path, {result["weather"]["station"]}</text>']
    for alt in (0, 30, 60):
        r = R * (90 - alt) / 90
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{_f(r)}" fill="none" stroke="#bbb" stroke-width="1"/>')
    for lab, ang in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        a = math.radians(ang); out.append(f'<text x="{_f(cx + (R + 14) * math.sin(a) - 4)}" y="{_f(cy - (R + 14) * math.cos(a) + 4)}" font-size="12" fill="#333">{lab}</text>')

    def pt(alt, az):
        r = R * (90 - alt) / 90; a = math.radians(az)
        return f"{_f(cx + r * math.sin(a))},{_f(cy - r * math.cos(a))}"
    for arc, col in zip(result["sunpath"]["arcs"], ("#c60", "#d00", "#c60", "#06c")):
        if arc["points"]:
            out.append(f'<polyline points="{" ".join(pt(p[1], p[2]) for p in arc["points"])}" fill="none" stroke="{col}" stroke-width="1.5"/>')
    for an in result["sunpath"]["analemmas"]:
        if an["points"]:
            out.append(f'<polyline points="{" ".join(pt(p[2], p[3]) for p in an["points"])}" fill="none" stroke="#999" stroke-width="0.8"/>')
    out.append(f'<text x="16" y="{H - 12}" font-size="10" fill="#555">ladybug Sunpath (NOAA), local standard time UTC+8; arcs 21 Mar, 21 Jun, 22 Sep, 21 Dec</text>')
    out.append("</svg>")
    return "\n".join(out)


def shadow_card(result: dict) -> str:
    rows = result["shadow"]["instants"]
    W, H = 520, 60 + 22 * len(rows)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">', f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           '<text x="16" y="24" font-size="15" fill="#111">Direct sun on the sensor plane at key instants</text>', '<text x="16" y="42" font-size="11" fill="#555">share of sensors lit by the sun (1.0 = all)</text>']
    for i, r in enumerate(rows):
        y = 60 + i * 22
        out.append(f'<text x="16" y="{y + 12}" font-size="11" fill="#111">{r["month"]:02d}-{r["day"]:02d} {r["hour"]:04.1f}h  alt {_f(r["altitude_deg"], 1)}° az {_f(r["azimuth_deg"], 1)}°</text>')
        out.append(f'<rect x="300" y="{y}" width="{_f(180 * r["lit_fraction"])}" height="14" fill="#f2b01e"/>')
        out.append(f'<text x="486" y="{y + 12}" font-size="11" fill="#111">{_f(r["lit_fraction"], 2)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def cards_bundle(result: dict, unit_envelope, north=None) -> str:
    """Single SVG document stacking the four cards (byte-deterministic)."""
    parts = [heatmap_card(result, unit_envelope, north=north)]
    for date, rec in sorted(result.get("solar_access", {}).items()):
        parts.append(heatmap_card(result, unit_envelope, title=f"Direct sun hours on {date}", unit_label="hours", values=rec["sun_hours"], north=north))
    parts += [sunpath_card(result), shadow_card(result)]
    y = 0
    inner = []
    W = 0
    for p in parts:
        w = int(p.split('width="')[1].split('"')[0]); h = int(p.split('height="')[1].split('"')[0])
        body = p[p.index(">") + 1: p.rindex("</svg>")]
        inner.append(f'<g transform="translate(0,{y})">{body}</g>')
        y += h + 16; W = max(W, w)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{y}" viewBox="0 0 {W} {y}">\n' + "\n".join(inner) + "\n</svg>\n"
