from __future__ import annotations

from typing import Any

from property_scan.common.output_contract import PropertyPlan, assignment_readiness_summary, validate_plan_contract


def build_assignment_status(plan: PropertyPlan) -> dict[str, Any]:
    """Build a reviewer-facing status artifact without overstating accuracy."""
    validate_plan_contract(plan)
    readiness = assignment_readiness_summary(plan)
    implemented = {
        "shared_output_contract": True,
        "photo_video_lidar_pipelines": True,
        "metric_depth_geometry": True,
        "whole_property_stitching": True,
        "confidence_and_quality_gates": True,
        "opening_evidence": True,
        "independent_ground_truth_comparison": True,
        "assignment_tolerance_rules": True,
    }
    blocked = [
        {
            "severity": "critical",
            "requirement": "assignment accuracy certification",
            "reason": "the supplied captures do not contain independent physical ground truth",
            "next_action": "collect measured wall, opening, and ceiling values and rerun the benchmark",
        },
    ]
    if not readiness["quality_gates"]["stitching"]:
        blocked.append({
            "severity": "high",
            "requirement": "whole-property drift gate",
            "reason": "stitching quality gate is not passing for this plan",
            "next_action": "capture overlap or doorway evidence and reduce layout drift",
        })
    if not readiness["quality_gates"]["room_geometry"]:
        blocked.append({
            "severity": "high",
            "requirement": "metric room geometry",
            "reason": "room geometry quality gate is not passing for this plan",
            "next_action": "improve qualified wall-plane coverage and footprint agreement",
        })
    return {
        "schema_version": "1.0.0",
        "property_id": plan.property_id,
        "capture_tier": plan.capture_tier,
        "implemented_requirements": implemented,
        "assignment_readiness": readiness,
        "blocked_requirements": blocked,
        "accuracy_claim_allowed": bool(plan.measurement_claims_validated),
        "overall_status": "ready" if plan.measurement_claims_validated else "diagnostic_only",
    }
