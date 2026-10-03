from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from property_scan.benchmark import (
    BenchmarkReport,
    ceiling_height_rule,
    opening_width_rule,
    wall_length_rule,
)
from property_scan.common.output_contract import PropertyPlan, validate_plan_contract


@dataclass(frozen=True)
class GroundTruthOpening:
    id: str
    type: str
    width_m: float
    height_m: float | None = None
    location: str | None = None


@dataclass(frozen=True)
class GroundTruthRoom:
    id: str
    ceiling_height_m: float
    wall_lengths_m: list[float]
    openings: list[GroundTruthOpening] = field(default_factory=list)
    floor_area_m2: float | None = None


@dataclass(frozen=True)
class GroundTruthManifest:
    source: str
    rooms: list[GroundTruthRoom]
    schema_version: str = "1.0.0"


def _number(value: Any, field_name: str, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field_name} must be a finite positive number")
    return number


def load_ground_truth(path: str | Path) -> GroundTruthManifest:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Ground-truth manifest does not exist: {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid ground-truth JSON: {manifest_path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Ground-truth manifest root must be an object")
    source = payload.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Ground-truth manifest requires a non-empty source")
    raw_rooms = payload.get("rooms")
    if not isinstance(raw_rooms, list) or not raw_rooms:
        raise ValueError("Ground-truth manifest requires a non-empty rooms list")

    rooms: list[GroundTruthRoom] = []
    room_ids: set[str] = set()
    for raw_room in raw_rooms:
        if not isinstance(raw_room, dict):
            raise ValueError("Each ground-truth room must be an object")
        room_id = raw_room.get("id")
        if not isinstance(room_id, str) or not room_id.strip():
            raise ValueError("Each ground-truth room requires a non-empty id")
        if room_id in room_ids:
            raise ValueError(f"Duplicate ground-truth room id: {room_id}")
        room_ids.add(room_id)

        raw_walls = raw_room.get("wall_lengths_m")
        if not isinstance(raw_walls, list) or not raw_walls:
            raise ValueError(f"Room {room_id} requires wall_lengths_m")
        wall_lengths = [_number(value, f"room {room_id} wall length") for value in raw_walls]

        raw_openings = raw_room.get("openings", [])
        if not isinstance(raw_openings, list):
            raise ValueError(f"Room {room_id} openings must be a list")
        openings: list[GroundTruthOpening] = []
        opening_ids: set[str] = set()
        for raw_opening in raw_openings:
            if not isinstance(raw_opening, dict):
                raise ValueError(f"Room {room_id} openings must contain objects")
            opening_id = raw_opening.get("id")
            opening_type = raw_opening.get("type")
            if not isinstance(opening_id, str) or not opening_id.strip():
                raise ValueError(f"Room {room_id} opening requires a non-empty id")
            if opening_id in opening_ids:
                raise ValueError(f"Duplicate opening id in room {room_id}: {opening_id}")
            if not isinstance(opening_type, str) or not opening_type.strip():
                raise ValueError(f"Opening {opening_id} requires a non-empty type")
            opening_ids.add(opening_id)
            openings.append(
                GroundTruthOpening(
                    id=opening_id,
                    type=opening_type,
                    width_m=_number(raw_opening.get("width_m"), f"opening {opening_id} width"),
                    height_m=_number(raw_opening.get("height_m"), f"opening {opening_id} height", allow_none=True),
                    location=raw_opening.get("location"),
                )
            )

        rooms.append(
            GroundTruthRoom(
                id=room_id,
                ceiling_height_m=_number(raw_room.get("ceiling_height_m"), f"room {room_id} ceiling height"),
                wall_lengths_m=wall_lengths,
                openings=openings,
                floor_area_m2=_number(raw_room.get("floor_area_m2"), f"room {room_id} floor area", allow_none=True),
            )
        )

    return GroundTruthManifest(
        source=source,
        rooms=rooms,
        schema_version=str(payload.get("schema_version", "1.0.0")),
    )


def _report_dict(report: BenchmarkReport) -> dict[str, Any]:
    return report.to_dict()


def validate_ground_truth_benchmark_report(report: dict[str, Any]) -> None:
    """Reject incomplete independent benchmark artifacts before persistence."""
    if report.get("schema_version") != "1.1.0":
        raise ValueError("ground-truth benchmark has an unsupported schema version")
    if report.get("validated_against_independent_ground_truth") is not True:
        raise ValueError("ground-truth benchmark must declare independent validation")
    if not isinstance(report.get("reports"), dict) or not report["reports"]:
        raise ValueError("ground-truth benchmark requires metric reports")
    if not isinstance(report.get("room_results"), list) or not report["room_results"]:
        raise ValueError("ground-truth benchmark requires room-level results")
    room_results = report["room_results"]
    room_ids = [item.get("room_id") for item in room_results if isinstance(item, dict)]
    if len(room_ids) != len(room_results) or any(not room_id for room_id in room_ids):
        raise ValueError("ground-truth room results require room ids")
    if len(set(room_ids)) != len(room_ids):
        raise ValueError("ground-truth benchmark contains duplicate room results")
    if report.get("rooms_evaluated") != len(room_results):
        raise ValueError("ground-truth room result count does not match rooms_evaluated")
    summary = report.get("metric_summary")
    if not isinstance(summary, dict) or summary.get("metric_count", 0) <= 0:
        raise ValueError("ground-truth benchmark requires metric summary")
    expected_metric_count = sum(
        len(item.get("metrics", []))
        for item in report["reports"].values()
        if isinstance(item, dict)
    )
    if summary.get("metric_count") != expected_metric_count:
        raise ValueError("ground-truth metric summary does not match metric reports")
    readiness = report.get("assignment_readiness")
    if not isinstance(readiness, dict) or "blockers" not in readiness or "next_action" not in readiness:
        raise ValueError("ground-truth benchmark requires assignment readiness details")
    gates = report.get("quality_gates")
    if not isinstance(gates, dict):
        raise ValueError("ground-truth benchmark requires quality gate status")
    for key in ("measurement_tolerances", "stitching", "room_geometry", "independent_ground_truth"):
        if key not in gates:
            raise ValueError(f"ground-truth quality gates are missing {key}")


def compare_plan_to_ground_truth(plan: PropertyPlan, manifest: GroundTruthManifest) -> dict[str, Any]:
    validate_plan_contract(plan)
    predicted_rooms = {room.id: room for room in plan.rooms}
    expected_rooms = {room.id: room for room in manifest.rooms}
    missing_rooms = sorted(set(expected_rooms) - set(predicted_rooms))
    unexpected_rooms = sorted(set(predicted_rooms) - set(expected_rooms))
    if missing_rooms or unexpected_rooms:
        raise ValueError(
            "Room ids do not match ground truth; "
            f"missing={missing_rooms}, unexpected={unexpected_rooms}"
        )

    ceiling_actual: list[float] = []
    ceiling_predicted: list[float] = []
    wall_actual: list[float] = []
    wall_predicted: list[float] = []
    opening_actual: list[float] = []
    opening_predicted: list[float] = []
    room_results: list[dict[str, Any]] = []

    for room_id, expected in expected_rooms.items():
        predicted = predicted_rooms[room_id]
        ceiling_actual.append(expected.ceiling_height_m)
        ceiling_predicted.append(predicted.ceiling_height.value)
        if len(expected.wall_lengths_m) != len(predicted.walls):
            raise ValueError(f"Wall count mismatch for room {room_id}")
        wall_actual.extend(sorted(expected.wall_lengths_m))
        wall_predicted.extend(sorted(wall.value for wall in predicted.walls))

        expected_openings = {(opening.type, opening.location): opening for opening in expected.openings}
        predicted_openings = {(opening.type, opening.location): opening for opening in predicted.openings}
        if set(expected_openings) != set(predicted_openings):
            raise ValueError(
                f"Opening mismatch for room {room_id}; "
                f"missing={sorted(set(expected_openings) - set(predicted_openings))}, "
                f"unexpected={sorted(set(predicted_openings) - set(expected_openings))}"
            )
        for key, expected_opening in expected_openings.items():
            opening_actual.append(expected_opening.width_m)
            opening_predicted.append(predicted_openings[key].width.value)
        room_reports = {
            "ceiling_height": _report_dict(
                ceiling_height_rule([expected.ceiling_height_m], [predicted.ceiling_height.value])
            ),
            "wall_length": _report_dict(
                wall_length_rule(
                    expected.wall_lengths_m,
                    [wall.value for wall in predicted.walls],
                )
            ),
        }
        if expected.openings:
            room_reports["opening_width"] = _report_dict(
                opening_width_rule(
                    [opening.width_m for opening in expected.openings],
                    [predicted_openings[(opening.type, opening.location)].width.value for opening in expected.openings],
                )
            )
        room_results.append({
            "room_id": room_id,
            "passed": all(item["summary"]["passed"] for item in room_reports.values()),
            "reports": room_reports,
        })

    reports = {
        "ceiling_height": _report_dict(ceiling_height_rule(ceiling_actual, ceiling_predicted)),
        "wall_length": _report_dict(wall_length_rule(wall_actual, wall_predicted)),
    }
    if opening_actual:
        reports["opening_width"] = _report_dict(opening_width_rule(opening_actual, opening_predicted))

    passed = all(report["summary"]["passed"] for report in reports.values())
    blockers = []
    if not passed:
        blockers.append("one or more assignment measurement tolerances failed")
    if not plan.quality_gates.get("stitching", False):
        blockers.append("stitching quality gate failed")
    if not plan.quality_gates.get("room_geometry", False):
        blockers.append("room geometry quality gate failed")
    total_metrics = sum(len(report["metrics"]) for report in reports.values())
    passed_metrics = sum(
        sum(1 for metric in report["metrics"] if metric["passed"])
        for report in reports.values()
    )
    passed_rooms = sum(1 for room in room_results if room["passed"])
    quality_gates = {
        "measurement_tolerances": passed,
        "stitching": bool(plan.quality_gates.get("stitching", False)),
        "room_geometry": bool(plan.quality_gates.get("room_geometry", False)),
        "independent_ground_truth": True,
    }
    ready = all(quality_gates.values())
    if ready:
        blockers = []
    return {
        "schema_version": "1.1.0",
        "ground_truth_source": manifest.source,
        "ground_truth_schema_version": manifest.schema_version,
        "capture_tier": plan.capture_tier,
        "rooms_evaluated": len(expected_rooms),
        "reports": reports,
        "room_results": room_results,
        "passed": passed,
        "metric_summary": {
            "case_count": len(reports),
            "metric_count": total_metrics,
            "passed_count": passed_metrics,
            "failed_count": total_metrics - passed_metrics,
            "pass_coverage": passed_metrics / total_metrics if total_metrics else 0.0,
        },
        "room_summary": {
            "room_count": len(room_results),
            "passed_count": passed_rooms,
            "failed_count": len(room_results) - passed_rooms,
            "pass_coverage": passed_rooms / len(room_results) if room_results else 0.0,
        },
        "quality_gates": quality_gates,
        "validated_against_independent_ground_truth": True,
        "assignment_readiness": {
            "ready": ready,
            "measurement_tolerances_passed": passed,
            "required_tolerances": {
                "opening_width_cm": 2.0,
                "opening_pass_fraction": 0.85,
                "ceiling_height_cm": 1.5,
            },
            "blockers": blockers,
            "next_action": (
                "assignment measurement claim is supported by all configured gates"
                if ready
                else
                "resolve the listed blockers and rerun the independent benchmark"
                if blockers
                else "eligible for assignment measurement claim review"
            ),
        },
    }
