import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.assignment_status import build_assignment_status
from property_scan.common.output_contract import Measurement, PropertyPlan, Room


class TestAssignmentStatus(unittest.TestCase):
    def test_status_is_diagnostic_without_ground_truth(self):
        plan = PropertyPlan(
            capture_tier="photo",
            property_id="demo",
            rooms=[Room("room_1", "Room", Measurement(10), Measurement(2.7))],
        )
        status = build_assignment_status(plan)
        self.assertEqual(status["overall_status"], "diagnostic_only")
        self.assertFalse(status["accuracy_claim_allowed"])
        self.assertTrue(status["implemented_requirements"]["assignment_tolerance_rules"])
        self.assertTrue(status["blocked_requirements"])


if __name__ == "__main__":
    unittest.main()
