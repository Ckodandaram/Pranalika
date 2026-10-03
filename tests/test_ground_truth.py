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
from property_scan.ground_truth import (
    GroundTruthManifest,
    GroundTruthRoom,
    compare_plan_to_ground_truth,
    load_ground_truth,
    validate_ground_truth_benchmark_report,
)


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
        self.assertTrue(report["validated_against_independent_ground_truth"])
        self.assertIn("assignment_readiness", report)
        self.assertFalse(report["assignment_readiness"]["ready"])
        self.assertEqual(report["metric_summary"]["metric_count"], 6)
        self.assertEqual(report["metric_summary"]["failed_count"], 0)
        self.assertEqual(report["room_results"][0]["room_id"], "room_1")
        self.assertTrue(report["room_results"][0]["passed"])
        validate_ground_truth_benchmark_report(report)

    def test_ground_truth_validator_rejects_missing_room_results(self):
        with self.assertRaisesRegex(ValueError, "room-level results"):
            validate_ground_truth_benchmark_report({
                "schema_version": "1.1.0",
                "validated_against_independent_ground_truth": True,
                "reports": {"ceiling_height": {}},
                "metric_summary": {"metric_count": 1},
                "assignment_readiness": {"blockers": [], "next_action": "none"},
            })

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

    def test_comparison_rejects_invalid_generated_measurement(self):
        manifest = GroundTruthManifest(
            source="survey",
            rooms=[GroundTruthRoom("room_1", 2.7, [4.0])],
        )
        plan = PropertyPlan(
            capture_tier="photo",
            property_id="test",
            rooms=[
                Room(
                    id="room_1",
                    name="Room",
                    floor_area=Measurement(0.0, "m2"),
                    ceiling_height=Measurement(2.7),
                    walls=[Measurement(4.0)],
                )
            ],
        )
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            compare_plan_to_ground_truth(plan, manifest)


if __name__ == "__main__":
    unittest.main()
