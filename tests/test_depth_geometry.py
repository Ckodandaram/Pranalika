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
    estimate_floor_aligned_footprint,
    estimate_wall_surface_geometry,
    estimate_vertical_wall_planes,
    estimate_trajectory_consistency,
    estimate_ransac_floor_plane_geometry,
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
        self.assertEqual(geometry["matched_frame_count"], 20)
        self.assertEqual(geometry["skipped_frame_count"], 0)
        self.assertGreater(geometry["confidence_filtered_point_count"], 0)

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

    def test_ransac_floor_plane_is_found_in_real_capture(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        geometry = estimate_ransac_floor_plane_geometry(detect_capture_profile(root))
        self.assertTrue(geometry["plane_found"])
        self.assertGreater(geometry["floor_inlier_count"], 0)
        self.assertGreaterEqual(geometry["normal_y"], 0.85)
        self.assertIn("normal_x", geometry)
        self.assertIn("normal_z", geometry)
        self.assertGreater(geometry["floor_x_extent_m"], 0.0)

    def test_floor_aligned_footprint_is_generated_from_real_capture(self):
        root = ROOT / "data" / "single_scan_floor_only" / "1a8384c3f6"
        footprint = estimate_floor_aligned_footprint(detect_capture_profile(root))
        self.assertTrue(footprint["footprint_found"])
        self.assertGreater(footprint["footprint_point_count"], 0)
        self.assertGreater(footprint["footprint_area_m2"], 0.0)
        self.assertGreaterEqual(len(footprint["polygon_xz_m"]), 3)
        self.assertEqual(len(footprint["horizontal_axis_u"]), 3)
        self.assertEqual(len(footprint["horizontal_axis_v"]), 3)

    def test_wall_surface_geometry_is_extracted_from_real_capture(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        geometry = estimate_wall_surface_geometry(detect_capture_profile(root))
        self.assertTrue(geometry["wall_surface_found"])
        self.assertGreater(geometry["wall_point_count"], 0)
        self.assertGreater(geometry["wall_vertical_extent_m"], 0.0)

    def test_vertical_wall_planes_are_reported_from_real_capture(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        result = estimate_vertical_wall_planes(detect_capture_profile(root))
        self.assertGreaterEqual(result["planes_found"], 0)
        self.assertEqual(result["matched_frame_count"], 20)
        self.assertIn("candidate_point_count", result)
        self.assertIn("best_candidate_inliers", result)
        for plane in result["planes"]:
            self.assertGreater(plane["inliers"], 100)
            self.assertGreater(plane["vertical_span_m"], 0.3)
            self.assertGreater(plane["horizontal_span_m"], 0.0)
            self.assertLess(plane["horizontal_min_m"], plane["horizontal_max_m"])
            self.assertLess(plane["vertical_min_m"], plane["vertical_max_m"])

    def test_trajectory_consistency_is_reported_for_real_capture(self):
        root = ROOT / "data" / "single_scan_with_ceiling" / "c7d28f72c6"
        result = estimate_trajectory_consistency(detect_capture_profile(root))
        self.assertTrue(result["has_trajectory"])
        self.assertGreater(result["path_length_m"], 0.0)
        self.assertGreaterEqual(result["return_error_m"], 0.0)


if __name__ == "__main__":
    unittest.main()
