from __future__ import annotations

import calendar
import hashlib
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from ladybug.dt import DateTime
from ladybug.epw import EPW
from ladybug.sunpath import Sunpath
from ladybug_geometry.geometry3d import Face3D, Point3D, Ray3D, Vector3D


ROOT = Path(__file__).parents[2]
WEATHER_PATH = ROOT / "data" / "weather" / "singapore-changi-2011-2025.epw"
WEATHER_SHA256 = "9293635032609058428c34809b0c2fa90178cb73d2aaf857f0918b46893bf60c"
LATITUDE = 1.295815
LONGITUDE = 103.809873
TIME_ZONE = 8
SEASONAL_DATES = ((3, 21), (6, 21), (9, 21), (12, 21))
FACADE_NORMALS = {
    "east": (1.0, 0.0),
    "north": (0.0, 1.0),
    "west": (-1.0, 0.0),
    "south": (0.0, -1.0),
}


def solar_altitude(latitude: float, longitude: float, value: str) -> float:
    stamp = datetime.fromisoformat(value)
    sun = Sunpath(latitude, longitude, TIME_ZONE).calculate_sun_from_date_time(
        DateTime(stamp.month, stamp.day, stamp.hour, stamp.minute)
    )
    return sun.altitude


@lru_cache(maxsize=1)
def _weather() -> tuple[dict[tuple[int, int, int], tuple[float, float]], dict]:
    epw = EPW(str(WEATHER_PATH))
    dni = epw.direct_normal_radiation
    dhi = epw.diffuse_horizontal_radiation
    values = {
        (dt.month, dt.day, dt.hour): (float(dni[index]), float(dhi[index]))
        for index, dt in enumerate(dni.datetimes)
    }
    source = {
        "station": "Singapore Changi International Airport 486980",
        "period": "TMYx 2011–2025",
        "source": "Climate.OneBuilding.Org",
        "sha256": WEATHER_SHA256,
    }
    return values, source


def _target_sensors(target: dict, columns: int = 16, rows: int = 8) -> tuple[list[Point3D], tuple[float, float]]:
    footprint = target["building"]["footprint"]
    xs = [point[0] for point in footprint]
    ys = [point[1] for point in footprint]
    normal = FACADE_NORMALS[target["facade"]]
    if normal[0]:
        fixed = (max(xs) if normal[0] > 0 else min(xs)) + normal[0] * 0.02
        span_min, span_max = min(ys), max(ys)
    else:
        fixed = (max(ys) if normal[1] > 0 else min(ys)) + normal[1] * 0.02
        span_min, span_max = min(xs), max(xs)

    position_factor = {"left": 0.25, "centre": 0.5, "right": 0.75}[target["position"]]
    centre = span_min + (span_max - span_min) * position_factor
    width = min(float(target["window_width"]), float(target["width"]), span_max - span_min)
    base_z = (float(target["storey"]) - 1) * 3.0 + float(target["sill_height"])
    height = float(target["window_height"])
    sensors = []
    for row in range(rows):
        z = base_z + height * (row + 0.5) / rows
        for column in range(columns):
            along = centre - width / 2 + width * (column + 0.5) / columns
            sensors.append(Point3D(fixed, along, z) if normal[0] else Point3D(along, fixed, z))
    return sensors, normal


def _ray_segment_distance(origin: Point3D, direction: Vector3D, a: list[float], b: list[float]) -> float | None:
    cross = direction.x * (b[1] - a[1]) - direction.y * (b[0] - a[0])
    if abs(cross) < 1e-9:
        return None
    ax = a[0] - origin.x
    ay = a[1] - origin.y
    ray_t = (ax * (b[1] - a[1]) - ay * (b[0] - a[0])) / cross
    edge_t = (ax * direction.y - ay * direction.x) / cross
    return ray_t if ray_t > 0.001 and 0 <= edge_t <= 1 else None


def _is_occluded(origin: Point3D, direction: Vector3D, buildings: list[dict]) -> bool:
    ray = Ray3D(origin, direction)
    for building in buildings:
        height = float(building["height_m"])
        footprint = building["footprint"]
        for a, b in zip(footprint, footprint[1:]):
            distance = _ray_segment_distance(origin, direction, a, b)
            if distance is None or origin.z + distance * direction.z > height:
                continue
            face = Face3D((Point3D(a[0], a[1], 0), Point3D(b[0], b[1], 0),
                           Point3D(b[0], b[1], height), Point3D(a[0], a[1], height)))
            if face.intersect_line_ray(ray) is not None:
                return True
    return False


def _sun(month: int, day: int, hour: int, minute: int = 0):
    return Sunpath(LATITUDE, LONGITUDE, TIME_ZONE).calculate_sun_from_date_time(
        DateTime(month, day, hour, minute)
    )


def _to_sun_vector(sun) -> Vector3D:
    return Vector3D(-sun.sun_vector.x, -sun.sun_vector.y, -sun.sun_vector.z)


def _sunlit_fraction(sensors: list[Point3D], sun, buildings: list[dict]) -> float:
    if not sun.is_during_day:
        return 0.0
    direction = _to_sun_vector(sun)
    visible = sum(not _is_occluded(sensor, direction, buildings) for sensor in sensors)
    return visible / len(sensors)


def _shadow(sensors: list[Point3D], buildings: list[dict]) -> dict:
    samples = []
    for hour in (9, 12, 15):
        sun = _sun(3, 21, hour)
        samples.append({
            "time": f"{hour:02d}:00",
            "altitude": round(sun.altitude, 2),
            "azimuth": round(sun.azimuth, 2),
            "sunlit_fraction": round(_sunlit_fraction(sensors, sun, buildings), 4),
        })
    return {"date": "2026-03-21", "timezone": "Asia/Singapore", "samples": samples}


def _solar_access(sensors: list[Point3D], buildings: list[dict]) -> dict:
    result = {}
    for month, day in SEASONAL_DATES:
        morning = afternoon = 0.0
        for half_hour in range(12, 38):
            hour, minute = divmod(half_hour * 30, 60)
            fraction = _sunlit_fraction(sensors, _sun(month, day, hour, minute), buildings)
            if hour < 13:
                morning += 0.5 * fraction
            else:
                afternoon += 0.5 * fraction
        result[f"2026-{month:02d}-{day:02d}"] = {
            "morning_hours": round(morning, 3),
            "afternoon_hours": round(afternoon, 3),
            "total_hours": round(morning + afternoon, 3),
            "interval_minutes": 30,
        }
    return result


def _radiation(sensors: list[Point3D], normal: tuple[float, float], buildings: list[dict]) -> dict:
    weather, _ = _weather()
    annual_wh = [0.0] * len(sensors)
    for month in range(1, 13):
        days = calendar.monthrange(2026, month)[1]
        for hour in range(7, 19):
            sun = _sun(month, 21, hour)
            if not sun.is_during_day:
                continue
            direction = _to_sun_vector(sun)
            dni, dhi = weather[(month, 21, hour)]
            incidence = max(0.0, normal[0] * direction.x + normal[1] * direction.y)
            diffuse = dhi * 0.5
            for index, sensor in enumerate(sensors):
                direct = 0.0 if incidence == 0 or _is_occluded(sensor, direction, buildings) else dni * incidence
                annual_wh[index] += (direct + diffuse) * days
    values = [round(value / 1000, 2) for value in annual_wh]
    return {
        "grid": [16, 8],
        "representative_days": 12,
        "sensor_values_kwh_m2": values,
        "minimum_kwh_m2": min(values),
        "maximum_kwh_m2": max(values),
        "average_kwh_m2": round(sum(values) / len(values), 2),
        "components": ["occluded direct DNI × incidence", "isotropic DHI × 0.5"],
        "limitations": ["no inter-reflection", "surrounding massing does not obstruct diffuse sky"],
    }


def analyse_scene(scene: dict) -> dict:
    sensors, normal = _target_sensors(scene["target"])
    buildings = [building for building in scene.get("buildings", [])
                 if building["id"] != scene["target"]["building"]["id"]]
    sunpath = []
    path = Sunpath(LATITUDE, LONGITUDE, TIME_ZONE)
    for month, day in SEASONAL_DATES:
        samples = []
        for hour in range(7, 19):
            sun = path.calculate_sun_from_date_time(DateTime(month, day, hour))
            if sun.is_during_day:
                samples.append({"hour": hour, "altitude": round(sun.altitude, 3), "azimuth": round(sun.azimuth, 3)})
        sunpath.append({"date": f"2026-{month:02d}-{day:02d}", "samples": samples})

    _, weather_source = _weather()
    result = {
        "method_version": "apartment-intelligence-solar-v2",
        "weather": weather_source,
        "sunpath": sunpath,
        "shadow": _shadow(sensors, buildings),
        "solar_access": _solar_access(sensors, buildings),
        "radiation": _radiation(sensors, normal, buildings),
    }
    digest_payload = {"scene": scene, "weather_sha256": WEATHER_SHA256, "result": result}
    result["digest"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result
