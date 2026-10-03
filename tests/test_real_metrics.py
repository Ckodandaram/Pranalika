import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.data_loader import confidence_quality_gate, discover_capture_profiles, summarize_capture_profile
from property_scan.pipeline.photo import build_photo_plan


class TestRealSampleMetrics(unittest.TestCase):
    def test_real_metrics_are_data_driven(self):
        profiles = discover_capture_profiles(ROOT / "data")
        metrics = {profile.scan_type: summarize_capture_profile(profile) for profile in profiles}

        self.assertGreater(metrics["floor_only"].estimated_ceiling_height_m, 1.0)
        self.assertGreater(metrics["with_ceiling"].estimated_ceiling_height_m, metrics["floor_only"].estimated_ceiling_height_m)
        self.assertGreater(metrics["single_room"].estimated_floor_area_m2, 8.0)
        self.assertGreater(metrics["single_room"].confidence_coverage, 0.0)

    def test_real_geometry_estimation_uses_capture_depth_signal(self):
        geometry = __import__("property_scan.data_loader", fromlist=["estimate_real_room_geometry"]).estimate_real_room_geometry(ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6")
        self.assertEqual(geometry["scan_type"], "with_ceiling")
        self.assertGreater(geometry["estimated_ceiling_height_m"], 2.5)
        self.assertGreater(geometry["confidence_coverage"], 0.0)

    def test_assignment_benchmark_runner_executes(self):
        from property_scan.benchmark_runner import run_assignment_benchmark

        report = run_assignment_benchmark(ROOT / "data")
        self.assertIn("opening_width", report)
        self.assertIn("ceiling_height", report)
        self.assertIn("wall_length", report)
        self.assertIn("repeatability", report)
        self.assertIn("reconstruction_quality", report)
        self.assertIn("validated_for_accuracy_claims", report["reconstruction_quality"]["summary"])
        self.assertIn("opening_evidence", report)
        self.assertFalse(report["opening_evidence"]["summary"]["validated_against_independent_ground_truth"])

    def test_confidence_quality_gate_flags_low_coverage(self):
        self.assertTrue(confidence_quality_gate(0.99)["passed"])
        self.assertFalse(confidence_quality_gate(0.90)["passed"])
        with self.assertRaises(ValueError):
            confidence_quality_gate(0.90, minimum_coverage=1.1)

    def test_photo_output_keeps_opening_candidate_evidence_inspectable(self):
        plan = build_photo_plan(ROOT / "data", property_id="real")
        candidate_items = [
            item
            for room in plan.rooms
            for item in room.scope_items
            if item["item"] == "wall_opening_candidate"
        ]
        for item in candidate_items:
            self.assertGreater(item["quantity"], 0.0)
            self.assertLess(item["start_m"], item["end_m"])
            self.assertGreaterEqual(item["confidence"], 0.0)
            self.assertLessEqual(item["confidence"], 1.0)

    def test_photo_output_exposes_metric_room_boundary_candidate(self):
        plan = build_photo_plan(ROOT / "data", property_id="real")
        boundary_items = [
            item
            for room in plan.rooms
            for item in room.scope_items
            if item["item"] == "room_boundary_candidate"
        ]
        self.assertEqual(len(boundary_items), len(plan.rooms))
        for item in boundary_items:
            self.assertGreater(item["quantity"], 0.0)
            self.assertGreaterEqual(len(item["polygon"]), 3)
            self.assertFalse(item["validated"])


if __name__ == "__main__":
    unittest.main()
