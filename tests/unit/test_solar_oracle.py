"""Solar oracles: Ladybug sunpath vs pvlib NREL SPA; unobstructed radiation vs EPW GHI."""
import math

import numpy as np
import pytest
from ladybug_geometry.geometry3d import Mesh3D, Point3D

from ai_solar.sky import sky_matrix
from ai_solar.study import mesh3d_from_trimesh, radiation_study
from ai_solar.sunpath import sun_at, sunpath_for
from ai_solar.weather import load_epw, weather_record

INSTANTS = [(3, 21, 12.0), (6, 21, 9.0), (6, 21, 15.0), (9, 22, 12.0), (12, 21, 10.0), (12, 21, 16.0), (1, 15, 8.0), (4, 10, 17.0), (7, 4, 13.0), (10, 20, 11.0), (11, 30, 14.0), (2, 14, 9.5)]


def test_sunpath_matches_pvlib_spa_within_0_05_deg():
    pvlib = pytest.importorskip("pvlib")
    import pandas as pd

    e = load_epw()
    sp = sunpath_for()
    lat, lon, tz = e.location.latitude, e.location.longitude, e.location.time_zone
    worst = 0.0
    for m, d, h in INSTANTS:
        s = sun_at(sp, m, d, h)
        t = pd.Timestamp(year=2017, month=m, day=d, hour=int(h), minute=int((h % 1) * 60), tz=f"Etc/GMT{-int(tz):+d}")  # Ladybug non-leap reference year
        pos = pvlib.solarposition.get_solarposition(pd.DatetimeIndex([t]), lat, lon, method="nrel_numpy")
        d_alt = abs(float(pos["apparent_elevation"].iloc[0]) - s["altitude_deg"])  # both include refraction
        d_az = abs((float(pos["azimuth"].iloc[0]) - s["azimuth_deg"] + 180) % 360 - 180)
        worst = max(worst, d_alt, d_az)
    assert worst <= 0.05, worst


def test_equinox_noon_altitude_near_zenith():
    sp = sunpath_for()
    best = max(sun_at(sp, 3, 21, h)["altitude_deg"] for h in np.arange(12.0, 14.0, 1 / 60))
    assert best >= 88.0


def test_unobstructed_horizontal_radiation_matches_epw_ghi_within_3_percent():
    sky = sky_matrix()
    ghi = weather_record()["annual_ghi_kwh_m2"]
    far = Mesh3D([Point3D(1000, 1000, -50), Point3D(1001, 1000, -50), Point3D(1001, 1001, -50)], [(0, 1, 2)])
    r = radiation_study(sky, [(0.0, 0.0, 10.0)], far, tag="oracle-ghi")
    sky_only = r["direct_kwh_m2"][0] + r["diffuse_kwh_m2"][0]
    assert abs(sky_only - ghi) / ghi <= 0.03, (sky_only, ghi)


def test_east_obstruction_cuts_morning_not_afternoon():
    import trimesh

    from ai_solar.study import direct_sun_study

    sp = sunpath_for()
    wall = trimesh.creation.box(extents=(1, 60, 60)); wall.apply_translation([10, 0, 30])
    ctx = mesh3d_from_trimesh(wall)
    res = direct_sun_study(sp, [(0.0, 0.0, 1.0)], ctx, dates=[(3, 21)], tag="oracle-east")["03-21"]
    bits = res["lit_matrix_packed"].split("|")[0]
    hours = res["instants"]
    morning = [b for b, h in zip(bits, hours) if h < 11]
    afternoon = [b for b, h in zip(bits, hours) if h > 13]
    assert "0" in morning and all(b == "1" for b in afternoon), (morning, afternoon)
