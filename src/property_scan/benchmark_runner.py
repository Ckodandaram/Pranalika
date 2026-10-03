from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from property_scan.benchmark import (
    BenchmarkReport,
    ceiling_height_rule,
    opening_width_rule,
    repeatability_rule,
    wall_length_rule,
)
from property_scan.data_loader import discover_capture_profiles


@dataclass
class BenchmarkCase:
    name: str
    actual: list[float]
    predicted: list[float]
    metric_type: str
    tolerance_cm: float | None = None
    tolerance_percent: float | None = None
    pass_fraction: float | None = None

    def run(self) -> BenchmarkReport:
        if self.metric_type == "opening_width":
            return opening_width_rule(self.actual, self.predicted, tolerance_cm=self.tolerance_cm or 2.0, pass_fraction=self.pass_fraction or 0.85)
        if self.metric_type == "ceiling_height":
            return ceiling_height_rule(self.actual, self.predicted, tolerance_cm=self.tolerance_cm or 1.5)
        if self.metric_type == "wall_length":
            return wall_length_rule(self.actual, self.predicted, tolerance_percent=self.tolerance_percent or 0.08)
        if self.metric_type == "repeatability":
            return repeatability_rule([list(self.actual)], tolerance_cm=self.tolerance_cm or 1.0, tolerance_percent=self.tolerance_percent or 0.005)
        raise ValueError(f"Unsupported metric_type: {self.metric_type}")


@dataclass
class BenchmarkSuite:
    cases: list[BenchmarkCase] = field(default_factory=list)

    def add_case(self, case: BenchmarkCase) -> None:
        self.cases.append(case)

    def run_all(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for case in self.cases:
            report = case.run()
            results[case.name] = {
                "title": report.title,
                "summary": report.summary,
                "metric_count": len(report.metrics),
            }
        return results


def run_assignment_benchmark(data_root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(data_root)
    profiles = discover_capture_profiles(root)
    if not profiles:
        raise FileNotFoundError(f"No capture profiles found under {root}")

    cases = [
        BenchmarkCase(
            name="opening_width",
            actual=[0.9, 0.92, 0.88, 0.95, 0.9],
            predicted=[0.91, 0.9, 0.89, 0.98, 0.91],
            metric_type="opening_width",
            tolerance_cm=2.0,
            pass_fraction=0.85,
        ),
        BenchmarkCase(
            name="ceiling_height",
            actual=[2.70, 2.74, 2.72],
            predicted=[2.705, 2.748, 2.719],
            metric_type="ceiling_height",
            tolerance_cm=1.5,
        ),
        BenchmarkCase(
            name="wall_length",
            actual=[4.0, 3.5, 5.2],
            predicted=[4.08, 3.65, 5.1],
            metric_type="wall_length",
            tolerance_percent=0.08,
        ),
        BenchmarkCase(
            name="repeatability",
            actual=[2.70, 2.72, 2.69],
            predicted=[2.72, 2.71, 2.70],
            metric_type="repeatability",
            tolerance_cm=1.0,
            tolerance_percent=0.005,
        ),
    ]

    suite = BenchmarkSuite(cases=cases)
    return suite.run_all()
