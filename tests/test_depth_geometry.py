import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.data_loader import (
    detect_capture_profile,
    estimate_projected_depth_geometry,
    estimate_pose_registered_depth_geometry,
    estimate_real_room_geometry,
    estimate_floor_plane_geometry,
    estimate_translated_depth_geometry,
)


class TestDepthGeometry(unittest.TestCase):
    def test_real_capture_depth_is_projected_using_camera_calibration(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        geometry = estimate_projected_depth_geometry(detect_capture_profile(root))
        self.assertGreater(geometry["projected_point_count"], 0)
        self.assertGreater(geometry["x_extent_m"], 0.0)
        self.assertGreater(geometry["y_extent_m"], 0.0)
        self.assertGreater(geometry["z_extent_m"], 0.0)

    def test_geometry_summary_exposes_projected_depth_diagnostics(self):
        root = ROOT / "data" / "single_room" / "c00a170fe1"
        summary = estimate_real_room_geometry(root)
        self.assertIn("projected_point_count", summary)
        self.assertGreater(summary["projected_point_count"], 0)
        self.assertGreater(summary["translated_depth_geometry"]["registered_point_count"], 0)

    def test_odometry_translation_is_applied_to_depth_samples(self):
        root = ROOT / "data" / "single_scan_floor_only" / "1a8384c3f6"
        geometry = estimate_translated_depth_geometry(detect_capture_profile(root))
        self.assertGreater(geometry["registered_point_count"], 0)
        self.assertGreater(geometry["x_extent_m"], 0.0)
        self.assertGreater(geometry["z_extent_m"], 0.0)

    def test_quaternion_pose_registration_uses_real_capture_data(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        geometry = estimate_pose_registered_depth_geometry(detect_capture_profile(root))
        self.assertGreater(geometry["registered_point_count"], 0)
        self.assertGreater(geometry["x_extent_m"], 0.0)
        self.assertGreater(geometry["y_extent_m"], 0.0)
        self.assertGreater(geometry["z_extent_m"], 0.0)

    def test_floor_candidate_is_extracted_from_registered_real_depth(self):
        root = ROOT / "data" / "single_scan_floor_only" / "1a8384c3f6"
        geometry = estimate_floor_plane_geometry(detect_capture_profile(root))
        self.assertGreater(geometry["floor_inlier_count"], 0)
        self.assertGreater(geometry["floor_x_extent_m"], 0.0)
        self.assertGreater(geometry["floor_z_extent_m"], 0.0)


if __name__ == "__main__":
    unittest.main()
