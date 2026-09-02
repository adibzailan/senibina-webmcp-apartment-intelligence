from __future__ import annotations

import math
import hashlib
import json
import argparse
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def compile_source(source_path: Path, config: dict[str, Any], diagnostics_dir: Path | None = None) -> dict[str, Any]:
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_hash != config.get("source_sha256"):
        raise ValueError("SOURCE_HASH_MISMATCH")
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("SOURCE_IMAGE_UNREADABLE")
    x, y, width, height = (int(value) for value in config["crop"])
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > image.shape[1] or y + height > image.shape[0]:
        raise ValueError("INVALID_SOURCE_CROP")
    crop = image[y:y + height, x:x + width]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.asarray(config["hsv_lower"], dtype=np.uint8),
        np.asarray(config["hsv_upper"], dtype=np.uint8),
    )
    compiled = compile_mask(mask, reference_area_m2=float(config["reference_area_m2"]))
    if diagnostics_dir is not None:
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(diagnostics_dir / "01-crop.png"), crop)
        cv2.imwrite(str(diagnostics_dir / "02-segmented-mask.png"), mask)
        aligned_mask = compiled["diagnostic_aligned_mask"]
        overlay = cv2.cvtColor(aligned_mask, cv2.COLOR_GRAY2BGR)
        pixels = np.asarray(compiled["polygon_aligned_px"], dtype=np.int32)
        cv2.polylines(overlay, [pixels], True, (12, 52, 230), 3, cv2.LINE_AA)
        cv2.imwrite(str(diagnostics_dir / "03-rationalized-overlay.png"), overlay)
    normalized, frontage_length = _normalize_frontage(compiled["polygon_local_m"])
    fixture: dict[str, Any] = {
        "schema": "apartment-intelligence.unit-plan.v1",
        "plan_id": config["plan_id"],
        "label": config.get("label", config["plan_id"]),
        "plan_state": "published_typical_reference",
        "source": {**config["source"], "page_image_sha256": source_hash},
        "reference_area_m2": float(config["reference_area_m2"]),
        "reference_area_state": "inferred_cross_checked",
        "polygon_local_m": normalized,
        "frontage": {
            "edge_index": 0,
            "length_m": round(frontage_length, 8),
            "derivation": "longest_supported_exterior_edge",
        },
        "derivation": {
            "method_version": "apartment-intelligence-floorplate-compiler-v1",
            "dominant_rotation_deg": compiled["dominant_rotation_deg"],
            "scale_m_per_pixel": compiled["scale_m_per_pixel"],
            "crop_xywh": list(config["crop"]),
            "segmentation_hsv": {"lower": list(config["hsv_lower"]), "upper": list(config["hsv_upper"])},
            "thresholds": {
                "minimum_mask_iou": 0.90,
                "maximum_area_change_fraction": 0.05,
                "minimum_vertices": 8,
                "maximum_vertices": 40,
                "maximum_boundary_rms_deviation_fraction": 0.02,
            },
        },
        "quality": compiled["quality"],
    }
    encoded = json.dumps(fixture, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    fixture["geometry_digest"] = hashlib.sha256(encoded).hexdigest()
    return fixture


def _largest_contour(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("NO_UNIT_REGION")
    return max(contours, key=cv2.contourArea)


def _cluster(values: list[int], tolerance: int) -> dict[int, int]:
    ordered = sorted(set(values))
    groups: list[list[int]] = []
    for value in ordered:
        if not groups or value - groups[-1][-1] > tolerance:
            groups.append([value])
        else:
            groups[-1].append(value)
    return {value: round(float(np.median(group))) for group in groups for value in group}


def _remove_collinear(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    changed = True
    output = points
    while changed and len(output) > 3:
        changed = False
        reduced: list[tuple[int, int]] = []
        for index, point in enumerate(output):
            previous = output[index - 1]
            following = output[(index + 1) % len(output)]
            if (previous[0] == point[0] == following[0]) or (previous[1] == point[1] == following[1]):
                changed = True
                continue
            reduced.append(point)
        output = reduced
    return output


def _signed_area(points: list[tuple[float, float]]) -> float:
    return sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    ) / 2


def _is_simple(points: list[tuple[int, int]]) -> bool:
    segments = list(zip(points, points[1:] + points[:1]))
    for index, first in enumerate(segments):
        for other_index, second in enumerate(segments):
            if other_index <= index or other_index in {index - 1, index + 1} or {index, other_index} == {0, len(segments) - 1}:
                continue
            if _segments_intersect(first[0], first[1], second[0], second[1]):
                return False
    return True


def _segments_intersect(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int], d: tuple[int, int]) -> bool:
    def orientation(p, q, r):
        value = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        return 0 if value == 0 else (1 if value > 0 else 2)
    return orientation(a, b, c) != orientation(a, b, d) and orientation(c, d, a) != orientation(c, d, b)


def _passes_quality_gate(vertex_count: int, mask_iou: float, area_change: float, boundary_deviation: float) -> bool:
    return 8 <= vertex_count <= 40 and mask_iou >= .90 and area_change <= .05 and boundary_deviation <= .02


def _normalize_frontage(points: list[list[float]]) -> tuple[list[list[float]], float]:
    candidates = []
    for index, (a, b) in enumerate(zip(points, points[1:] + points[:1])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            continue
        tangent = (dx / length, dy / length)
        inward = (-tangent[1], tangent[0])
        midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        distances = [(point[0] - midpoint[0]) * inward[0] + (point[1] - midpoint[1]) * inward[1] for point in points]
        if min(distances) >= -1e-7:
            candidates.append((length, -index, index, tangent, inward, midpoint))
    if not candidates:
        raise ValueError("NO_SUPPORTED_FRONTAGE")
    length, _, index, tangent, inward, midpoint = max(candidates)
    ordered = points[index:] + points[:index]
    normalized = [[
        float(round((point[0] - midpoint[0]) * tangent[0] + (point[1] - midpoint[1]) * tangent[1], 8)),
        float(round((point[0] - midpoint[0]) * inward[0] + (point[1] - midpoint[1]) * inward[1], 8)),
    ] for point in ordered]
    if length < 4.0:
        raise ValueError("APERTURE_DOES_NOT_FIT")
    return normalized, length


def _mask_iou(mask: np.ndarray, polygon: list[tuple[int, int]]) -> float:
    rendered = np.zeros_like(mask)
    cv2.fillPoly(rendered, [np.asarray(polygon, dtype=np.int32)], 255)
    source_region = mask > 0
    candidate_region = rendered > 0
    union = int(np.count_nonzero(source_region | candidate_region))
    return int(np.count_nonzero(source_region & candidate_region)) / union if union else 0.0


def _boundary_rms_deviation(contour: np.ndarray, polygon: list[tuple[int, int]], short_dimension: int) -> float:
    squared_distances = []
    for x, y in contour.reshape(-1, 2):
        distance = min(
            _distance_point_to_segment((float(x), float(y)), a, b)
            for a, b in zip(polygon, polygon[1:] + polygon[:1])
        )
        squared_distances.append(distance * distance)
    return math.sqrt(sum(squared_distances) / len(squared_distances)) / short_dimension


def _distance_point_to_segment(point: tuple[float, float], a: tuple[int, int], b: tuple[int, int]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    amount = 0.0 if denominator == 0 else max(0.0, min(1.0,
        ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denominator))
    return math.hypot(point[0] - (a[0] + amount * dx), point[1] - (a[1] + amount * dy))


def _resolve_diagonal_corners(mask: np.ndarray, points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    output: list[tuple[int, int]] = []
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        output.append(point)
        if point[0] == following[0] or point[1] == following[1]:
            continue
        candidates = [(point[0], following[1]), (following[0], point[1])]
        scored = []
        for candidate in candidates:
            trial = output + [candidate] + points[index + 1:]
            scored.append((_mask_iou(mask, trial), candidate))
        output.append(max(scored)[1])
    return _remove_collinear(output)


def compile_mask(mask: np.ndarray, *, reference_area_m2: float) -> dict[str, Any]:
    if mask.ndim != 2 or reference_area_m2 <= 0:
        raise ValueError("INVALID_COMPILER_INPUT")
    binary = np.where(mask > 0, 255, 0).astype(np.uint8)
    close_size = max(5, round(min(binary.shape) * 0.045))
    close_size += 1 - close_size % 2
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_size, close_size))
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, open_kernel)
    contour = _largest_contour(cleaned)
    silhouette = np.zeros_like(cleaned)
    cv2.drawContours(silhouette, [contour], -1, 255, thickness=cv2.FILLED)
    centre = (silhouette.shape[1] / 2, silhouette.shape[0] / 2)
    angle = float(cv2.minAreaRect(contour)[2])
    if angle < -45:
        angle += 90
    rotation = cv2.getRotationMatrix2D(centre, angle, 1.0)
    aligned = cv2.warpAffine(silhouette, rotation, (silhouette.shape[1], silhouette.shape[0]), flags=cv2.INTER_NEAREST)
    aligned_contour = _largest_contour(aligned)
    epsilon = max(1.5, min(aligned.shape) * 0.008)
    approximated = cv2.approxPolyDP(aligned_contour, epsilon, True).reshape(-1, 2)
    tolerance = max(2, round(min(aligned.shape) * 0.0125))
    x_map = _cluster([int(point[0]) for point in approximated], tolerance)
    y_map = _cluster([int(point[1]) for point in approximated], tolerance)
    polygon = _remove_collinear([(x_map[int(x)], y_map[int(y)]) for x, y in approximated])
    polygon = _resolve_diagonal_corners(aligned, polygon)
    if len(polygon) < 4:
        raise ValueError("RATIONALIZATION_FAILED")
    if any(a[0] != b[0] and a[1] != b[1] for a, b in zip(polygon, polygon[1:] + polygon[:1])):
        raise ValueError("NON_ORTHOGONAL_BOUNDARY")

    mask_iou = _mask_iou(aligned, polygon)
    raw_area = float(cv2.contourArea(aligned_contour))
    polygon_area = abs(_signed_area([(float(x), float(y)) for x, y in polygon]))
    area_change = abs(polygon_area - raw_area) / raw_area if raw_area else math.inf
    boundary_deviation = _boundary_rms_deviation(aligned_contour, polygon, min(aligned.shape))
    if not _is_simple(polygon) or not _passes_quality_gate(len(polygon), mask_iou, area_change, boundary_deviation):
        raise ValueError("QUALITY_GATE_FAILED")

    scale = math.sqrt(reference_area_m2 / polygon_area)
    centroid = np.mean(np.asarray(polygon, dtype=float), axis=0)
    local = [[float(round((x - centroid[0]) * scale, 8)), float(round((centroid[1] - y) * scale, 8))] for x, y in polygon]
    if _signed_area([(point[0], point[1]) for point in local]) < 0:
        local.reverse()
    return {
        "polygon_local_m": local,
        "area_m2": float(round(abs(_signed_area([(point[0], point[1]) for point in local])), 8)),
        "dominant_rotation_deg": round(angle, 8),
        "polygon_aligned_px": [[int(x), int(y)] for x, y in polygon],
        "scale_m_per_pixel": round(scale, 10),
        "diagnostic_aligned_mask": aligned,
        "quality": {
            "mask_iou": round(mask_iou, 8),
            "area_change_fraction": round(area_change, 8),
            "boundary_rms_deviation_fraction": round(boundary_deviation, 8),
            "vertex_count": len(polygon),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a reviewed Dawson brochure plan into deterministic unit geometry.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path)
    arguments = parser.parse_args()
    config = json.loads(arguments.config.read_text(encoding="utf-8"))
    fixture = compile_source(arguments.source, config, arguments.diagnostics)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {
        "schema": "apartment-intelligence.unit-plan-receipt.v1",
        "plan_id": fixture["plan_id"],
        "compiler_version": fixture["derivation"]["method_version"],
        "source_page_image_sha256": fixture["source"]["page_image_sha256"],
        "source_pdf_sha256": fixture["source"].get("upstream_pdf_sha256"),
        "reference_area_m2": fixture["reference_area_m2"],
        "quality": fixture["quality"],
        "geometry_digest": fixture["geometry_digest"],
    }
    arguments.receipt.parent.mkdir(parents=True, exist_ok=True)
    arguments.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
