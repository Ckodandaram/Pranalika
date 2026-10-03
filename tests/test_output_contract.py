import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.cli import main
from property_scan.pipeline import build_lidar_plan, build_photo_plan, build_video_plan


class TestPropertyPlanContract(unittest.TestCase):
    def test_photo_plan_has_required_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            room_a = Path(tmpdir) / "room_a"
            room_b = Path(tmpdir) / "room_b"
            room_a.mkdir()
            room_b.mkdir()
            (room_a / "img1.jpg").write_bytes(b"fake")
            (room_a / "img2.jpg").write_bytes(b"fake")
            (room_b / "img1.jpg").write_bytes(b"fake")
            plan = build_photo_plan(tmpdir, property_id="demo")
            payload = plan.to_dict()
            self.assertIn("rooms", payload)
            self.assertIn("whole_property_connections", payload)
            self.assertIn("stitching_notes", payload)
            self.assertTrue(any("stitching connected=True" in note for note in payload["stitching_notes"]))
            self.assertGreater(len(payload["rooms"]), 0)
            self.assertEqual(payload["capture_tier"], "photo")

    def test_video_plan_has_measurements(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "walkthrough.mp4"
            video_path.write_bytes(b"fake video")
            plan = build_video_plan(video_path, property_id="demo")
            room = plan.rooms[0]
            self.assertIn("floor_area", room.to_dict())
            self.assertGreater(len(room.openings), 0)

    def test_lidar_plan_has_damage_and_confidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = build_lidar_plan(tmpdir, property_id="demo")
            self.assertTrue(any(room.damage for room in plan.rooms))
            room = plan.rooms[0]
            self.assertIn("confidence", room.floor_area.to_dict())

    def test_cli_writes_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            room_dir = Path(tmpdir) / "room_1"
            room_dir.mkdir()
            (room_dir / "img1.jpg").write_bytes(b"fake")
            output_file = Path(tmpdir) / "plan.json"
            argv = ["property_scan", "--tier", "photo", "--input", str(room_dir.parent), "--output", str(output_file)]
            import sys as _sys
            _sys.argv = argv
            exit_code = main()
            self.assertEqual(exit_code, 0)
            self.assertTrue(output_file.exists())
            payload = json.loads(output_file.read_text(encoding="utf-8"))
            self.assertIn("rooms", payload)


if __name__ == "__main__":
    unittest.main()
