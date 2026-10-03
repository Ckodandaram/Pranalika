import tempfile
import unittest
from pathlib import Path

from property_scan.arkitscenes import convert_capture


class ArkitScenesAdapterTests(unittest.TestCase):
    def test_converts_axis_angle_trajectory_and_intrinsics(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "raw"
            (source / "lowres_depth").mkdir(parents=True)
            (source / "confidence").mkdir()
            (source / "lowres_wide_intrinsics").mkdir()
            (source / "lowres_depth" / "capture_10.0.png").write_bytes(b"depth")
            (source / "confidence" / "capture_10.0.png").write_bytes(b"confidence")
            (source / "lowres_wide.traj").write_text("10.0 0 0 0 -1 -2 -3\n", encoding="utf-8")
            (source / "lowres_wide_intrinsics" / "capture.pincam").write_text(
                "256 192 210.099 210.099 127.489 97.8931\n",
                encoding="utf-8",
            )

            output = convert_capture(source, Path(temporary) / "normalized")

            self.assertEqual(
                (output / "odometry.csv").read_text(encoding="utf-8").splitlines()[1],
                "capture_10.0,1.0,2.0,3.0,0.0,0.0,0.0,1.0",
            )
            self.assertEqual(
                (output / "camera_matrix.csv").read_text(encoding="utf-8").splitlines()[0],
                "210.099,0.0,127.489",
            )
            self.assertTrue((output / "confidence" / "capture_10.0.png").exists())
