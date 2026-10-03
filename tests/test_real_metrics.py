import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.data_loader import discover_capture_profiles, summarize_capture_profile


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


if __name__ == "__main__":
    unittest.main()
