from __future__ import annotations

import argparse
import json
from pathlib import Path

from property_scan.ground_truth import (
    compare_plan_to_ground_truth,
    load_ground_truth,
    validate_ground_truth_benchmark_report,
)
from property_scan.benchmark_runner import run_assignment_benchmark, validate_assignment_benchmark_report
from property_scan.pipeline import build_lidar_plan, build_photo_plan, build_video_plan
from property_scan.common.output_contract import validate_plan_contract
from property_scan.assignment_status import build_assignment_status


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a common property floor-plan output from a capture tier.")
    parser.add_argument("--tier", choices=["photo", "video", "lidar"], required=True, help="Capture tier to process")
    parser.add_argument("--input", required=True, help="Input directory or file; for photo it is a room folder root, for video a .mp4, for lidar a capture directory")
    parser.add_argument("--output", required=True, help="JSON output path")
    parser.add_argument("--property-id", default="demo_property", help="Identifier for the output property")
    parser.add_argument("--ground-truth", help="Optional independently measured JSON manifest used to benchmark the generated plan")
    parser.add_argument("--benchmark-output", help="Optional JSON path for the ground-truth comparison report")
    parser.add_argument("--status-output", help="Optional JSON path for the reviewer-facing assignment status report")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.tier == "photo":
        plan = build_photo_plan(args.input, args.property_id)
    elif args.tier == "video":
        plan = build_video_plan(args.input, args.property_id)
    else:
        plan = build_lidar_plan(args.input, args.property_id)

    output_path = Path(args.output)
    validate_plan_contract(plan)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    print(f"Wrote plan to {output_path}")
    status_path = Path(args.status_output) if args.status_output else output_path.with_name(f"{output_path.stem}.status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(build_assignment_status(plan), indent=2), encoding="utf-8")
    print(f"Wrote assignment status to {status_path}")
    if args.ground_truth:
        report = compare_plan_to_ground_truth(plan, load_ground_truth(args.ground_truth))
        if report["metric_summary"]["metric_count"] == 0:
            raise ValueError("ground-truth benchmark produced no metrics")
        validate_ground_truth_benchmark_report(report)
        plan.quality_gates["independent_ground_truth"] = bool(report["passed"])
        plan.measurement_claims_validated = bool(
            report["passed"]
            and plan.quality_gates.get("stitching", False)
            and plan.quality_gates.get("room_geometry", False)
        )
        readiness = report["assignment_readiness"]
        readiness["ready"] = plan.measurement_claims_validated
        if plan.measurement_claims_validated:
            readiness["blockers"] = []
            readiness["next_action"] = "assignment measurement claim is supported by the configured gates"
        elif "stitching quality gate failed" not in readiness["blockers"] and not plan.quality_gates.get("stitching", False):
            readiness["blockers"].append("stitching quality gate failed")
        if "room geometry quality gate failed" not in readiness["blockers"] and not plan.quality_gates.get("room_geometry", False):
            readiness["blockers"].append("room geometry quality gate failed")
        output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
        status_path.write_text(json.dumps(build_assignment_status(plan), indent=2), encoding="utf-8")
        benchmark_path = Path(args.benchmark_output) if args.benchmark_output else output_path.with_name(f"{output_path.stem}.benchmark.json")
        benchmark_path.parent.mkdir(parents=True, exist_ok=True)
        benchmark_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote ground-truth benchmark to {benchmark_path}")
    elif args.benchmark_output:
        if args.tier != "photo":
            raise ValueError("--benchmark-output without --ground-truth is supported for the photo data root only")
        report = run_assignment_benchmark(args.input)
        validate_assignment_benchmark_report(report)
        benchmark_path = Path(args.benchmark_output)
        benchmark_path.parent.mkdir(parents=True, exist_ok=True)
        benchmark_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote assignment benchmark to {benchmark_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
