import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.benchmark_runner import validate_assignment_benchmark_report


class TestBenchmarkArtifactContract(unittest.TestCase):
    def test_rejects_proxy_report_claiming_ground_truth(self):
        report = {
            "opening_width": {"metrics": []},
            "ceiling_height": {"metrics": []},
            "wall_length": {"metrics": []},
            "repeatability": {"metrics": []},
            "report_schema_version": {"value": "1.2.0"},
            "report_provenance": {"independent_ground_truth": True},
            "assignment_readiness": {
                "ready": False,
                "validated_against_independent_ground_truth": True,
                "blockers": [],
                "next_action": "none",
            },
        }
        with self.assertRaisesRegex(ValueError, "independent_ground_truth=false"):
            validate_assignment_benchmark_report(report)

    def test_rejects_report_without_metric_details(self):
        report = {
            "opening_width": {},
            "ceiling_height": {"metrics": []},
            "wall_length": {"metrics": []},
            "repeatability": {"metrics": []},
            "report_schema_version": {"value": "1.2.0"},
            "report_provenance": {"independent_ground_truth": False},
            "assignment_readiness": {
                "ready": False,
                "validated_against_independent_ground_truth": False,
                "blockers": [],
                "next_action": "none",
            },
        }
        with self.assertRaisesRegex(ValueError, "opening_width requires metric details"):
            validate_assignment_benchmark_report(report)


if __name__ == "__main__":
    unittest.main()
