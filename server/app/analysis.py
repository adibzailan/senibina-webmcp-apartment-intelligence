from __future__ import annotations

import calendar
import hashlib
import json
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from ladybug.dt import DateTime
from ladybug.epw import EPW
from ladybug.sunpath import Sunpath
from ladybug_geometry.geometry3d import Face3D, Point3D, Ray3D, Vector3D


ROOT = Path(__file__).parents[2]
WEATHER_PATH = ROOT / "data" / "weather" / "singapore-changi-2011-2025.epw"
UNIT_PLAN_PATH = ROOT / "data" / "fixtures" / "unit-plans" / "skyville-dawson-4room-type-a-v1.json"
UNIT_PLAN = json.loads(UNIT_PLAN_PATH.read_text(encoding="utf-8"))
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


def _inside_polygon(point: tuple[float, float], footprint: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for a, b in zip(footprint, footprint[1:]):
        if (a[1] > y) != (b[1] > y):
            crossing = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing:
                inside = not inside
    return inside


def _edge_frame(a: list[float], b: list[float], footprint: list[list[float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    tangent = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    candidate = (tangent[1], -tangent[0])
    midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    sample = (midpoint[0] + candidate[0] * 0.05, midpoint[1] + candidate[1] * 0.05)
    outward = candidate if not _inside_polygon(sample, footprint) else (-candidate[0], -candidate[1])
    return tangent, outward


def _distance_to_segment(point: tuple[float, float], a: list[float], b: list[float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    amount = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length_sq))
    return math.hypot(point[0] - (a[0] + amount * dx), point[1] - (a[1] + amount * dy))


def _project_to_segment(point: tuple[float, float], a: list[float], b: list[float]) -> tuple[float, float]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length_sq = dx * dx + dy * dy
    amount = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length_sq))
    return a[0] + amount * dx, a[1] + amount * dy


def derive_plate(target: dict) -> dict:
    footprint = target["building"]["footprint"]
    xs = [point[0] for point in footprint]
    ys = [point[1] for point in footprint]
    cardinal = FACADE_NORMALS[target["facade"]]
    factor = {"left": 0.25, "centre": 0.5, "right": 0.75}[target["position"]]
    if cardinal[0]:
        along = min(ys) + (max(ys) - min(ys)) * factor
        origin = Point3D((max(xs) + 1 if cardinal[0] > 0 else min(xs) - 1), along, 0)
    else:
        along = min(xs) + (max(xs) - min(xs)) * factor
        origin = Point3D(along, (max(ys) + 1 if cardinal[1] > 0 else min(ys) - 1), 0)
    plan_points = UNIT_PLAN["polygon_local_m"]
    frontage_length = float(UNIT_PLAN["frontage"]["length_m"])
    window_width = float(target["window_width"])
    if window_width > frontage_length + 1e-9:
        raise ValueError("APERTURE_DOES_NOT_FIT")
    candidates = []
    for index, (a, b) in enumerate(zip(footprint, footprint[1:])):
        edge_length = math.hypot(b[0] - a[0], b[1] - a[1])
        if edge_length + 1e-9 < frontage_length:
            continue
        tangent, normal = _edge_frame(a, b, footprint)
        alignment = normal[0] * cardinal[0] + normal[1] * cardinal[1]
        if alignment < .5:
            continue
        midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        candidates.append((math.hypot(midpoint[0] - origin.x, midpoint[1] - origin.y), -alignment, -edge_length, index))
    if not candidates:
        raise ValueError("PLAN_PLACEMENT_OUTSIDE_FOOTPRINT")
    _, _, _, edge_index = min(candidates)
    a, b = footprint[edge_index], footprint[edge_index + 1]
    tangent, normal = _edge_frame(a, b, footprint)
    edge_length = math.hypot(b[0] - a[0], b[1] - a[1])
    factor = {"left": .25, "centre": .5, "right": .75}[target["position"]]
    margin = frontage_length / (2 * edge_length)
    amount = max(margin, min(1 - margin, factor))
    hit = (a[0] + (b[0] - a[0]) * amount, a[1] + (b[1] - a[1]) * amount)
    inward_xy = (-normal[0], -normal[1])
    mirror_factor = -1 if target.get("mirrored", False) else 1
    transformed = [
        (hit[0] + tangent[0] * x * mirror_factor + inward_xy[0] * y,
         hit[1] + tangent[1] * x * mirror_factor + inward_xy[1] * y)
        for x, y in plan_points
    ]
    sample_total = sample_inside = 0
    min_x, max_x = min(point[0] for point in plan_points), max(point[0] for point in plan_points)
    min_y, max_y = min(point[1] for point in plan_points), max(point[1] for point in plan_points)
    for local_y in _sample_range(min_y, max_y, .25):
        for local_x in _sample_range(min_x, max_x, .25):
            if not _inside_polygon((local_x, local_y), [*plan_points, plan_points[0]]):
                continue
            sample_total += 1
            world = (hit[0] + tangent[0] * local_x * mirror_factor + inward_xy[0] * local_y,
                     hit[1] + tangent[1] * local_x * mirror_factor + inward_xy[1] * local_y)
            sample_inside += int(_inside_polygon(world, footprint))
    containment = sample_inside / sample_total if sample_total else 0
    if containment < .95:
        raise ValueError("PLAN_PLACEMENT_OUTSIDE_FOOTPRINT")

    floor_z = (float(target["storey"]) - 1) * 3.0
    elevation = floor_z + 0.02
    spacing = 0.5
    columns, rows = math.ceil((max_x - min_x) / spacing), math.ceil((max_y - min_y) / spacing)
    if columns * rows > 256:
        spacing = 1.0
        columns, rows = math.ceil((max_x - min_x) / spacing), math.ceil((max_y - min_y) / spacing)
    cell_width = (max_x - min_x) / columns
    cell_depth = (max_y - min_y) / rows
    sensors = []
    mask = []
    for row in range(rows):
        v = min_y + cell_depth * (row + 0.5)
        for column in range(columns):
            u = min_x + cell_width * (column + 0.5)
            x = hit[0] + tangent[0] * u * mirror_factor + inward_xy[0] * v
            y = hit[1] + tangent[1] * u * mirror_factor + inward_xy[1] * v
            sensors.append([x, y, elevation])
            mask.append(1 if _inside_polygon((u, v), [*plan_points, plan_points[0]]) else 0)
    if not any(mask):
        raise ValueError("PLAN_PLACEMENT_OUTSIDE_FOOTPRINT")
    cell_area = cell_width * cell_depth
    aperture = {
        "centre_xyz": [hit[0], hit[1], floor_z + float(target["sill_height"]) + float(target["window_height"]) / 2],
        "width_m": window_width,
        "height_m": float(target["window_height"]),
        "sill_m": float(target["sill_height"]),
    }
    return {
        "plane": "finished_floor",
        "plane_offset_m": 0.02,
        "elevation_m": elevation,
        "outline_xy": [[round(x, 6), round(y, 6)] for x, y in [*transformed, transformed[0]]],
        "outline_xyz": [[round(x, 6), round(y, 6), elevation] for x, y in [*transformed, transformed[0]]],
        "anchor_xy": [round(hit[0], 6), round(hit[1], 6)],
        "wall_direction": [round(tangent[0], 8), round(tangent[1], 8)],
        "normal": [round(normal[0], 8), round(normal[1], 8)],
        "normal_state": "sourced_edge",
        "plan": {
            "plan_id": UNIT_PLAN["plan_id"],
            "label": UNIT_PLAN["label"],
            "source_state": UNIT_PLAN["plan_state"],
            "fixture_digest": UNIT_PLAN["geometry_digest"],
            "source": UNIT_PLAN["source"],
        },
        "reference_area_m2": UNIT_PLAN["reference_area_m2"],
        "sampled_area_m2": round(sum(mask) * cell_area, 3),
        "placement": {"state": "inferred_transformed_reference", "mirrored": bool(target.get("mirrored", False)),
                      "containment_fraction": round(containment, 6), "edge_index": edge_index},
        "grid": [columns, rows],
        "spacing_m": spacing,
        "grid_origin_xyz": [round(hit[0] + tangent[0] * min_x * mirror_factor + inward_xy[0] * min_y, 6),
                            round(hit[1] + tangent[1] * min_x * mirror_factor + inward_xy[1] * min_y, 6), elevation],
        "grid_u_vector": [round(tangent[0] * cell_width * mirror_factor, 8), round(tangent[1] * cell_width * mirror_factor, 8), 0.0],
        "grid_v_vector": [round(inward_xy[0] * cell_depth, 8), round(inward_xy[1] * cell_depth, 8), 0.0],
        "mask": mask,
        "sensor_xyz": [[round(value, 6) for value in sensor] for sensor in sensors],
        "sensor_count": sum(mask),
        "usable_area_m2": round(sum(mask) * cell_area, 3),
        "cell_area_m2": cell_area,
        "aperture": aperture,
        "assumptions": [
            "published typical 4-room reference; not a verified Block 87 or storey-30 stack",
            "reference boundary uniformly scaled to 87 m²",
            "ground-level footprint reused at the selected storey",
            "open plan with no internal partitions",
            "one confirmed exterior window band",
            "no balcony slab or overhang",
        ],
    }


def _sample_range(start: float, stop: float, spacing: float) -> list[float]:
    count = max(1, math.ceil((stop - start) / spacing))
    return [start + (stop - start) * (index + .5) / count for index in range(count)]


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


def _aperture_hit(sensor: Point3D, direction: Vector3D, plate: dict) -> Point3D | None:
    normal = plate["normal"]
    facing = direction.x * normal[0] + direction.y * normal[1]
    if facing <= 1e-9:
        return None
    anchor = plate["anchor_xy"]
    distance = ((anchor[0] - sensor.x) * normal[0] + (anchor[1] - sensor.y) * normal[1]) / facing
    if distance <= 0:
        return None
    hit = Point3D(sensor.x + direction.x * distance, sensor.y + direction.y * distance, sensor.z + direction.z * distance)
    tangent = plate["wall_direction"]
    along = (hit.x - anchor[0]) * tangent[0] + (hit.y - anchor[1]) * tangent[1]
    aperture = plate["aperture"]
    floor_z = plate["elevation_m"] - plate["plane_offset_m"]
    bottom = floor_z + aperture["sill_m"]
    top = bottom + aperture["height_m"]
    return hit if abs(along) <= aperture["width_m"] / 2 + 1e-7 and bottom - 1e-7 <= hit.z <= top + 1e-7 else None


def _visible_through_aperture(sensor: Point3D, direction: Vector3D, plate: dict, buildings: list[dict]) -> int:
    hit = _aperture_hit(sensor, direction, plate)
    if hit is None:
        return 0
    origin = Point3D(hit.x + direction.x * 0.02, hit.y + direction.y * 0.02, hit.z + direction.z * 0.02)
    return 0 if _is_occluded(origin, direction, buildings) else 1


def _sensor_visibility(sensors: list[Point3D], mask: list[int], plate: dict, sun, buildings: list[dict]) -> list[int]:
    if not sun.is_during_day:
        return [0] * len(sensors)
    direction = _to_sun_vector(sun)
    return [
        _visible_through_aperture(sensor, direction, plate, buildings) if mask[index] else 0
        for index, sensor in enumerate(sensors)
    ]


def _masked_average(values: list[float | int], mask: list[int]) -> float:
    selected = [value for value, included in zip(values, mask) if included]
    return sum(selected) / len(selected)


def _shadow(sensors: list[Point3D], plate: dict, buildings: list[dict]) -> dict:
    samples = []
    for hour in (9, 12, 15):
        sun = _sun(3, 21, hour)
        visibility = _sensor_visibility(sensors, plate["mask"], plate, sun, buildings)
        fraction = _masked_average(visibility, plate["mask"])
        samples.append({
            "time": f"{hour:02d}:00",
            "altitude": round(sun.altitude, 2),
            "azimuth": round(sun.azimuth, 2),
            "sensor_values": visibility,
            "sunlit_fraction": round(fraction, 4),
            "sun_patch_area_m2": round(sum(visibility) * plate["cell_area_m2"], 3),
        })
    return {"date": "2026-03-21", "timezone": "Asia/Singapore", "samples": samples}


def _solar_access(sensors: list[Point3D], plate: dict, buildings: list[dict]) -> dict:
    result = {}
    for month, day in SEASONAL_DATES:
        morning = afternoon = 0.0
        sensor_hours = [0.0] * len(sensors)
        for half_hour in range(12, 38):
            hour, minute = divmod(half_hour * 30, 60)
            visibility = _sensor_visibility(sensors, plate["mask"], plate, _sun(month, day, hour, minute), buildings)
            fraction = _masked_average(visibility, plate["mask"])
            if hour < 13:
                morning += 0.5 * fraction
            else:
                afternoon += 0.5 * fraction
            for index, visible in enumerate(visibility):
                sensor_hours[index] += 0.5 * visible
        result[f"2026-{month:02d}-{day:02d}"] = {
            "morning_hours": round(morning, 3),
            "afternoon_hours": round(afternoon, 3),
            "total_hours": round(morning + afternoon, 3),
            "interval_minutes": 30,
            "sensor_hours": sensor_hours,
        }
    return result


def _diffuse_view_factor(sensor: Point3D, plate: dict, buildings: list[dict]) -> float:
    aperture = plate["aperture"]
    anchor = plate["anchor_xy"]
    tangent = plate["wall_direction"]
    normal = plate["normal"]
    floor_z = plate["elevation_m"] - plate["plane_offset_m"]
    patch_area = aperture["width_m"] * aperture["height_m"] / 12
    factor = 0.0
    for row in range(3):
        z = floor_z + aperture["sill_m"] + aperture["height_m"] * (row + 0.5) / 3
        for column in range(4):
            along = -aperture["width_m"] / 2 + aperture["width_m"] * (column + 0.5) / 4
            sample = Point3D(anchor[0] + tangent[0] * along, anchor[1] + tangent[1] * along, z)
            dx, dy, dz = sample.x - sensor.x, sample.y - sensor.y, sample.z - sensor.z
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)
            if distance <= 1e-9:
                continue
            direction = Vector3D(dx / distance, dy / distance, dz / distance)
            cosine_floor = max(0.0, direction.z)
            cosine_aperture = max(0.0, direction.x * normal[0] + direction.y * normal[1])
            if not cosine_floor or not cosine_aperture:
                continue
            origin = Point3D(sample.x + direction.x * 0.02, sample.y + direction.y * 0.02, sample.z + direction.z * 0.02)
            if not _is_occluded(origin, direction, buildings):
                factor += cosine_floor * cosine_aperture * patch_area / (math.pi * distance * distance)
    return min(1.0, factor)


def _radiation(sensors: list[Point3D], plate: dict, buildings: list[dict]) -> dict:
    weather, _ = _weather()
    annual_wh = [0.0] * len(sensors)
    diffuse_factors = [
        _diffuse_view_factor(sensor, plate, buildings) if plate["mask"][index] else 0.0
        for index, sensor in enumerate(sensors)
    ]
    for month in range(1, 13):
        days = calendar.monthrange(2026, month)[1]
        for hour in range(7, 19):
            sun = _sun(month, 21, hour)
            if not sun.is_during_day:
                continue
            direction = _to_sun_vector(sun)
            dni, dhi = weather[(month, 21, hour)]
            incidence = max(0.0, direction.z)
            for index, sensor in enumerate(sensors):
                if not plate["mask"][index]:
                    continue
                direct = dni * incidence * _visible_through_aperture(sensor, direction, plate, buildings)
                diffuse = dhi * diffuse_factors[index]
                annual_wh[index] += (direct + diffuse) * days
    values = [round(value / 1000, 2) for value in annual_wh]
    included_values = [value for value, included in zip(values, plate["mask"]) if included]
    return {
        "grid": plate["grid"],
        "representative_days": 12,
        "sensor_values_kwh_m2": values,
        "minimum_kwh_m2": min(included_values),
        "maximum_kwh_m2": max(included_values),
        "average_kwh_m2": round(sum(included_values) / len(included_values), 2),
        "components": [
            "direct DNI × horizontal incidence through confirmed aperture, occluded",
            "isotropic DHI × visible sensor-to-aperture configuration factor",
        ],
        "limitations": [
            "no glazing transmittance",
            "no inter-reflection",
            "open plan with no internal partitions",
            "no balcony slab or overhang",
            "12 representative monthly days",
            "consumer decision support, not professional daylight certification",
        ],
    }


def analyse_scene(scene: dict) -> dict:
    plate = derive_plate(scene["target"])
    sensors = [Point3D(*point) for point in plate["sensor_xyz"]]
    target_building = scene["target"]["building"]
    buildings = [target_building, *[
        building for building in scene.get("buildings", []) if building["id"] != target_building["id"]
    ]]
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
        "method_version": "apartment-intelligence-solar-v5",
        "weather": weather_source,
        "plate": plate,
        "sunpath": sunpath,
        "shadow": _shadow(sensors, plate, buildings),
        "solar_access": _solar_access(sensors, plate, buildings),
        "radiation": _radiation(sensors, plate, buildings),
    }
    digest_payload = {"scene": scene, "weather_sha256": WEATHER_SHA256, "result": result}
    result["digest"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result
