from __future__ import annotations

import math
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from data.scripts.compile_unit_plan import _is_simple, _passes_quality_gate, compile_mask, compile_source


class FloorplateCompilerTests(unittest.TestCase):
    def test_rotated_noisy_orthogonal_mask_becomes_a_simple_orthogonal_polygon(self) -> None:
        mask = np.zeros((240, 260), dtype=np.uint8)
        source = np.array(
            [[45, 45], [205, 45], [205, 125], [170, 125], [170, 195], [100, 195], [100, 170], [45, 170]],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [source], 255)
        rotation = cv2.getRotationMatrix2D((130, 120), 4.0, 1.0)
        mask = cv2.warpAffine(mask, rotation, (260, 240), flags=cv2.INTER_NEAREST)
        mask[36:39, 116:123] = 255
        mask[188:191, 82:87] = 0

        result = compile_mask(mask, reference_area_m2=87.0)

        polygon = result["polygon_local_m"]
        self.assertGreaterEqual(len(polygon), 8)
        self.assertLessEqual(len(polygon), 12)
        self.assertAlmostEqual(result["area_m2"], 87.0, places=6)
        self.assertGreaterEqual(result["quality"]["mask_iou"], 0.90)
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            self.assertTrue(math.isclose(dx, 0.0, abs_tol=1e-8) or math.isclose(dy, 0.0, abs_tol=1e-8))

    def test_non_orthogonal_source_fails_the_automatic_quality_gate(self) -> None:
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.fillPoly(mask, [np.array([[30, 170], [100, 25], [170, 170]], dtype=np.int32)], 255)

        with self.assertRaisesRegex(ValueError, "QUALITY_GATE_FAILED"):
            compile_mask(mask, reference_area_m2=87.0)

    def test_wall_width_gaps_are_closed_before_the_outer_silhouette_is_rationalized(self) -> None:
        mask = np.zeros((240, 260), dtype=np.uint8)
        outline = np.array(
            [[45, 45], [205, 45], [205, 125], [170, 125], [170, 195], [100, 195], [100, 170], [45, 170]],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [outline], 255)
        cv2.line(mask, (45, 105), (205, 105), 0, 7)
        cv2.line(mask, (120, 45), (120, 170), 0, 7)
        mask[101:109, 78:94] = 255
        mask[72:88, 116:124] = 255

        result = compile_mask(mask, reference_area_m2=87.0)

        self.assertGreaterEqual(result["quality"]["mask_iou"], 0.90)
        self.assertGreaterEqual(len(result["polygon_local_m"]), 8)

    def test_changed_source_hash_is_rejected_before_segmentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            source.write_bytes(b"not the reviewed source")
            config = {"source_sha256": "0" * 64}

            with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
                compile_source(source, config)

    def test_coloured_source_compiles_to_a_deterministic_frontage_normalized_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            image = np.full((240, 260, 3), 255, dtype=np.uint8)
            polygon = np.array(
                [[45, 45], [205, 45], [205, 125], [170, 125], [170, 195], [100, 195], [100, 170], [45, 170]],
                dtype=np.int32,
            )
            cv2.fillPoly(image, [polygon], (105, 170, 220))
            cv2.imwrite(str(source), image)
            config = {
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "crop": [0, 0, 260, 240],
                "hsv_lower": [5, 30, 100],
                "hsv_upper": [40, 255, 255],
                "reference_area_m2": 87.0,
                "plan_id": "test-plan",
                "source": {"title": "Synthetic test", "page": 1, "state": "test"},
            }

            first = compile_source(source, config)
            second = compile_source(source, config)

            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertEqual(first["schema"], "apartment-intelligence.unit-plan.v1")
            self.assertEqual(first["plan_id"], "test-plan")
            self.assertAlmostEqual(first["reference_area_m2"], 87.0)
            self.assertEqual(first["frontage"]["edge_index"], 0)
            self.assertGreaterEqual(first["frontage"]["length_m"], 4.0)
            self.assertGreater(first["derivation"]["scale_m_per_pixel"], 0)
            self.assertEqual(first["derivation"]["crop_xywh"], [0, 0, 260, 240])
            self.assertEqual(first["source"]["page_image_sha256"], config["source_sha256"])
            self.assertTrue(all(point[1] >= -1e-8 for point in first["polygon_local_m"]))
            self.assertEqual(len(first["geometry_digest"]), 64)

    def test_every_numeric_acceptance_threshold_is_enforced(self) -> None:
        self.assertTrue(_passes_quality_gate(8, .90, .05, .02))
        self.assertFalse(_passes_quality_gate(7, .99, 0, 0))
        self.assertFalse(_passes_quality_gate(41, .99, 0, 0))
        self.assertFalse(_passes_quality_gate(8, .899, 0, 0))
        self.assertFalse(_passes_quality_gate(8, .99, .051, 0))
        self.assertFalse(_passes_quality_gate(8, .99, 0, .021))

    def test_self_intersecting_orthogonal_polygon_is_not_simple(self) -> None:
        crossing = [(0, 0), (4, 0), (4, 4), (2, 4), (2, -2), (0, -2)]
        self.assertFalse(_is_simple(crossing))


if __name__ == "__main__":
    unittest.main()
