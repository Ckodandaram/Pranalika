from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class MetricResult:
    metric: str
    actual: float
    predicted: float
    error: float
    pass_threshold: float
    passed: bool
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "actual": self.actual,
            "predicted": self.predicted,
            "error": self.error,
            "pass_threshold": self.pass_threshold,
            "passed": self.passed,
            "notes": self.notes,
        }


@dataclass
class BenchmarkReport:
    title: str
    metrics: List[MetricResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def add_metric(self, metric: MetricResult) -> None:
        self.metrics.append(metric)

    def summary_with_metrics(self) -> Dict[str, Any]:
        passed_count = sum(1 for metric in self.metrics if metric.passed)
        metric_count = len(self.metrics)
        return {
            **self.summary,
            "metric_count": metric_count,
            "passed_count": passed_count,
            "failed_count": metric_count - passed_count,
            "pass_coverage": passed_count / metric_count if metric_count else 0.0,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "metrics": [m.to_dict() for m in self.metrics],
            "summary": self.summary_with_metrics(),
        }


def opening_width_rule(actual_widths: Iterable[float], predicted_widths: Iterable[float], tolerance_cm: float = 2.0, pass_fraction: float = 0.85) -> BenchmarkReport:
    actual = list(actual_widths)
    predicted = list(predicted_widths)
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted opening width lists must be the same length")

    results: List[MetricResult] = []
    passing = 0
    for i, (actual_value, predicted_value) in enumerate(zip(actual, predicted), start=1):
        error = abs(actual_value - predicted_value)
        passed = error <= tolerance_cm / 100.0
        if passed:
            passing += 1
        results.append(
            MetricResult(
                metric=f"opening_width_{i}",
                actual=actual_value,
                predicted=predicted_value,
                error=error,
                pass_threshold=tolerance_cm / 100.0,
                passed=passed,
                notes="opening width check",
            )
        )

    fraction = passing / len(actual) if actual else 0.0
    report = BenchmarkReport(
        title="Opening width accuracy",
        metrics=results,
        summary={
            "required_fraction": pass_fraction,
            "observed_fraction": fraction,
            "threshold_cm": tolerance_cm,
            "passed": fraction >= pass_fraction,
        },
    )
    return report


def ceiling_height_rule(actual_heights: Iterable[float], predicted_heights: Iterable[float], tolerance_cm: float = 1.5) -> BenchmarkReport:
    actual = list(actual_heights)
    predicted = list(predicted_heights)
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted ceiling height lists must be the same length")

    results: List[MetricResult] = []
    all_passed = True
    for i, (actual_value, predicted_value) in enumerate(zip(actual, predicted), start=1):
        error = abs(actual_value - predicted_value)
        passed = error <= tolerance_cm / 100.0
        all_passed = all_passed and passed
        results.append(
            MetricResult(
                metric=f"ceiling_height_{i}",
                actual=actual_value,
                predicted=predicted_value,
                error=error,
                pass_threshold=tolerance_cm / 100.0,
                passed=passed,
                notes="ceiling height check",
            )
        )

    return BenchmarkReport(
        title="Ceiling height accuracy",
        metrics=results,
        summary={
            "threshold_cm": tolerance_cm,
            "passed": all_passed,
        },
    )


def wall_length_rule(actual_lengths: Iterable[float], predicted_lengths: Iterable[float], tolerance_percent: float = 0.08) -> BenchmarkReport:
    actual = list(actual_lengths)
    predicted = list(predicted_lengths)
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted wall length lists must be the same length")

    results: List[MetricResult] = []
    all_passed = True
    for i, (actual_value, predicted_value) in enumerate(zip(actual, predicted), start=1):
        if actual_value == 0:
            error = 0.0
        else:
            error = abs(actual_value - predicted_value) / actual_value
        passed = error <= tolerance_percent
        all_passed = all_passed and passed
        results.append(
            MetricResult(
                metric=f"wall_length_{i}",
                actual=actual_value,
                predicted=predicted_value,
                error=error,
                pass_threshold=tolerance_percent,
                passed=passed,
                notes="wall-length percentage error check",
            )
        )

    return BenchmarkReport(
        title="Wall length accuracy",
        metrics=results,
        summary={
            "threshold_percent": tolerance_percent,
            "passed": all_passed,
        },
    )


def repeatability_rule(samples: Iterable[List[float]], tolerance_cm: float = 1.0, tolerance_percent: float = 0.005) -> BenchmarkReport:
    sample_groups = list(samples)
    results: List[MetricResult] = []
    all_passed = True
    for group_index, group in enumerate(sample_groups, start=1):
        if not group or len(group) < 2:
            continue
        baseline = group[0]
        spread = max(abs(value - baseline) for value in group[1:])
        relative = spread / max(abs(baseline), 1e-9)
        passed = spread <= tolerance_cm / 100.0 or relative <= tolerance_percent
        all_passed = all_passed and passed
        results.append(
            MetricResult(
                metric=f"repeatability_group_{group_index}",
                actual=baseline,
                predicted=max(group[1:]) if group[1:] else baseline,
                error=spread,
                pass_threshold=max(tolerance_cm / 100.0, tolerance_percent * max(abs(baseline), 1e-9)),
                passed=passed,
                notes="repeatability check; same room repeated at same tier must be stable",
            )
        )

    return BenchmarkReport(
        title="Repeatability",
        metrics=results,
        summary={
            "threshold_cm": tolerance_cm,
            "threshold_percent": tolerance_percent,
            "passed": all_passed,
        },
    )


def benchmark_summary(report: BenchmarkReport) -> Dict[str, Any]:
    return report.summary
