import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.data_loader import discover_capture_profiles


class TestRealCaptureProfiles(unittest.TestCase):
    def test_sample_datasets_are_detected_as_real_captures(self):
        profiles = discover_capture_profiles(ROOT / "data")
        names = {profile.scan_type for profile in profiles}
        self.assertIn("single_room", names)
        self.assertIn("floor_only", names)
        self.assertIn("with_ceiling", names)
        self.assertEqual(len(profiles), 3)

    def test_capture_profiles_include_motion_and_depth_metadata(self):
        profiles = discover_capture_profiles(ROOT / "data")
        by_type = {profile.scan_type: profile for profile in profiles}
        self.assertGreater(by_type["single_room"].frame_count, 0)
        self.assertTrue(by_type["single_room"].has_depth)
        self.assertTrue(by_type["single_room"].has_confidence)
        self.assertGreater(by_type["with_ceiling"].total_motion_m, 0.0)


if __name__ == "__main__":
    unittest.main()
