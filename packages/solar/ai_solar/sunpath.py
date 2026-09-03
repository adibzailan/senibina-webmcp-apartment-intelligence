"""Sun positions from Ladybug's Sunpath (NOAA-based), plus sunpath diagram data."""
from __future__ import annotations

from ladybug.sunpath import Sunpath
from ladybug.dt import DateTime

from .weather import load_epw

KEY_DATES = [(3, 21), (6, 21), (9, 22), (12, 21)]


def sunpath_for(epw_path: str | None = None) -> Sunpath:
    e = load_epw(epw_path)
    return Sunpath.from_location(e.location)


def sun_at(sp: Sunpath, month: int, day: int, hour: float) -> dict:
    s = sp.calculate_sun(month, day, hour)
    v = s.sun_vector  # points from sun toward the ground (Ladybug convention)
    return {"month": month, "day": day, "hour": hour, "altitude_deg": round(s.altitude, 4), "azimuth_deg": round(s.azimuth, 4), "is_up": bool(s.is_during_day), "vector": [round(v.x, 6), round(v.y, 6), round(v.z, 6)]}


def sunpath_record(sp: Sunpath, step_minutes: int = 30) -> dict:
    """Day arcs for four key dates plus hourly analemmas (a compact sunpath diagram)."""
    arcs = []
    for m, d in KEY_DATES:
        pts = []
        h = 0.0
        while h < 24.0:
            s = sun_at(sp, m, d, h)
            if s["is_up"]:
                pts.append([s["hour"], s["altitude_deg"], s["azimuth_deg"]])
            h += step_minutes / 60.0
        arcs.append({"date": f"{m:02d}-{d:02d}", "points": pts})
    analemmas = []
    for hour in range(6, 20):
        pts = []
        for m in range(1, 13):
            for day in (1, 15):
                s = sun_at(sp, m, day, float(hour))
                if s["is_up"]:
                    pts.append([m, day, s["altitude_deg"], s["azimuth_deg"]])
        analemmas.append({"hour": hour, "points": pts})
    return {"method": "ladybug.sunpath.Sunpath (NOAA solar position), local standard time UTC+8", "arcs": arcs, "analemmas": analemmas}
