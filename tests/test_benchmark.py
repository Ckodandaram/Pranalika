import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.benchmark import (
    ceiling_height_rule,
    opening_width_rule,
    repeatability_rule,
    wall_length_rule,
)


class TestBenchmarkRules(unittest.TestCase):
    def test_opening_width_rule_passes_threshold(self):
        report = opening_width_rule([0.90, 0.80, 1.10], [0.902, 0.80, 1.11], tolerance_cm=2.0, pass_fraction=0.85)
        self.assertTrue(report.summary["passed"])
        summary = report.to_dict()["summary"]
        self.assertEqual(summary["metric_count"], 3)
        self.assertEqual(summary["passed_count"], 3)
        self.assertEqual(summary["failed_count"], 0)
        self.assertEqual(summary["pass_coverage"], 1.0)

    def test_ceiling_height_rule_requires_tight_tolerance(self):
        report = ceiling_height_rule([2.70, 2.75], [2.705, 2.752])
        self.assertTrue(report.summary["passed"])

    def test_wall_length_rule_rejects_large_percentage_error(self):
        report = wall_length_rule([4.0, 3.5], [4.4, 3.85], tolerance_percent=0.08)
        self.assertFalse(report.summary["passed"])
        self.assertEqual(report.to_dict()["summary"]["failed_count"], 2)

    def test_repeatability_rule_flags_inconsistent_room_scans(self):
        report = repeatability_rule([[2.70, 2.75, 2.69]], tolerance_cm=1.0, tolerance_percent=0.005)
        self.assertFalse(report.summary["passed"])


if __name__ == "__main__":
    unittest.main()
