import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room
from property_scan.ground_truth import compare_plan_to_ground_truth, load_ground_truth


class TestGroundTruth(unittest.TestCase):
    def test_manifest_loads_and_compares_against_generated_plan(self):
        manifest = {
            "schema_version": "1.0.0",
            "source": "independent tape and laser measurements",
            "rooms": [
                {
                    "id": "room_1",
                    "ceiling_height_m": 2.7,
                    "wall_lengths_m": [4.0, 3.0, 4.0, 3.0],
                    "openings": [{"id": "door_1", "type": "door", "width_m": 0.9, "location": "south"}],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ground_truth.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded = load_ground_truth(path)

        plan = PropertyPlan(
            capture_tier="photo",
            property_id="test",
            rooms=[
                Room(
                    id="room_1",
                    name="Room 1",
                    floor_area=Measurement(12.0, "m2"),
                    ceiling_height=Measurement(2.7),
                    walls=[Measurement(value) for value in [4.0, 3.0, 4.0, 3.0]],
                    openings=[Opening("opening_1", "door", Measurement(0.9), Measurement(2.0), "south")],
                )
            ],
        )
        report = compare_plan_to_ground_truth(plan, loaded)
        self.assertTrue(report["passed"])
        self.assertEqual(report["rooms_evaluated"], 1)
        self.assertIn("opening_width", report["reports"])

    def test_manifest_rejects_duplicate_room_ids(self):
        payload = {
            "source": "survey",
            "rooms": [
                {"id": "room_1", "ceiling_height_m": 2.7, "wall_lengths_m": [4.0]},
                {"id": "room_1", "ceiling_height_m": 2.7, "wall_lengths_m": [4.0]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ground_truth.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate ground-truth room id"):
                load_ground_truth(path)


if __name__ == "__main__":
    unittest.main()
