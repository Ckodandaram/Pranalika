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
from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, validate_plan_contract


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

    def test_plan_contract_rejects_duplicate_rooms(self):
        room = Room("room_1", "Room", Measurement(10), Measurement(2.7))
        with self.assertRaisesRegex(ValueError, "duplicate room id"):
            validate_plan_contract(PropertyPlan("photo", "demo", [room, room]))

    def test_plan_contract_rejects_invalid_measurements(self):
        room = Room("room_1", "Room", Measurement(0), Measurement(2.7))
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            validate_plan_contract(PropertyPlan("photo", "demo", [room]))

    def test_plan_contract_rejects_opening_outside_host_wall(self):
        room = Room(
            "room_1",
            "Room",
            Measurement(10),
            Measurement(2.7),
            walls=[Measurement(1.0)],
            openings=[
                Opening(
                    "opening_1",
                    "door",
                    Measurement(0.8),
                    Measurement(2.0),
                    "south",
                    wall_index=0,
                    position_ratio=0.1,
                )
            ],
        )
        with self.assertRaisesRegex(ValueError, "opening interval exceeds"):
            validate_plan_contract(PropertyPlan("photo", "demo", [room]))

    def test_plan_contract_rejects_unknown_connection_room(self):
        room = Room("room_1", "Room", Measurement(10), Measurement(2.7))
        plan = PropertyPlan(
            "photo",
            "demo",
            [room],
            whole_property_connections=[{"from": "room_1", "to": "room_2"}],
        )
        with self.assertRaisesRegex(ValueError, "unknown room"):
            validate_plan_contract(plan)
            self.assertIn("whole_property_connections", payload)
            self.assertIn("stitching_notes", payload)
            self.assertTrue(any("stitching connected=True" in note for note in payload["stitching_notes"]))
            self.assertIn("quality_gates", payload)
            self.assertFalse(payload["measurement_claims_validated"])
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
            self.assertFalse(room.openings[0].validated)
            self.assertIn("source", room.openings[0].to_dict())
            self.assertIn("wall_index", room.openings[0].to_dict())
            self.assertIn("position_ratio", room.openings[0].to_dict())
            self.assertTrue(any("stitching connected=True" in note for note in plan.stitching_notes))
            self.assertIn("quality_gates", plan.to_dict())

    def test_lidar_plan_has_damage_and_confidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = build_lidar_plan(tmpdir, property_id="demo")
            self.assertTrue(any(room.damage for room in plan.rooms))
            room = plan.rooms[0]
            self.assertIn("confidence", room.floor_area.to_dict())
            self.assertTrue(any("stitching quality gate passed=True" in note for note in plan.stitching_notes))
            self.assertFalse(plan.to_dict()["measurement_claims_validated"])
            self.assertFalse(plan.rooms[0].openings[0].validated)

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

    def test_cli_writes_assignment_benchmark_for_photo_data_root(self):
        data_root = ROOT / "data"
        output_file = Path(tempfile.gettempdir()) / "property_scan_plan.json"
        benchmark_file = Path(tempfile.gettempdir()) / "property_scan_assignment_benchmark.json"
        argv = [
            "property_scan",
            "--tier", "photo",
            "--input", str(data_root),
            "--output", str(output_file),
            "--benchmark-output", str(benchmark_file),
        ]
        import sys as _sys
        _sys.argv = argv
        try:
            self.assertEqual(main(), 0)
            report = json.loads(benchmark_file.read_text(encoding="utf-8"))
            self.assertIn("reconstruction_quality", report)
            self.assertIn("opening_evidence", report)
            self.assertIn("report_provenance", report)
        finally:
            output_file.unlink(missing_ok=True)
            benchmark_file.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
