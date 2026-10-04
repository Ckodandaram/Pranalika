from __future__ import annotations

from pathlib import Path

from property_scan.common.output_contract import PropertyPlan


def _find_normalized_sidecar(video_path: Path) -> Path | None:
    candidates = []
    if video_path.is_dir():
        candidates.append(video_path)
    else:
        candidates.extend(
            [
                video_path.with_suffix(""),
                video_path.parent / f"{video_path.stem}_normalized",
                video_path.parent / "normalized",
            ]
        )
    for candidate in candidates:
        if (candidate / "depth").is_dir() and (candidate / "odometry.csv").exists():
            return candidate
    return None


def build_video_plan(video_path: str | Path, property_id: str = "property") -> PropertyPlan:
    """Build a video plan from a video plus calibrated depth/pose sidecar.

    COLMAP-style feature matching can recover structure from RGB-only video, but
    metric wall and ceiling measurements still require scale. The normalized
    sidecar is the supported metric input until a COLMAP binary and calibration
    provider are configured.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video does not exist: {video_path}")
    sidecar = _find_normalized_sidecar(path)
    if sidecar is None:
        raise ValueError(
            "video reconstruction requires a normalized metric sidecar containing "
            "depth/ and odometry.csv; RGB-only video cannot produce metric assignment measurements"
        )
    from property_scan.pipeline.photo import build_photo_plan

    photo_plan = build_photo_plan(sidecar, property_id)
    return PropertyPlan(
        capture_tier="video",
        property_id=photo_plan.property_id,
        rooms=photo_plan.rooms,
        whole_property_connections=photo_plan.whole_property_connections,
        layout_drift_m=photo_plan.layout_drift_m,
        stitching_notes=[
            "video reconstruction consumed calibrated depth and pose sidecar data",
            *photo_plan.stitching_notes,
        ],
        quality_gates=photo_plan.quality_gates,
        measurement_claims_validated=False,
    )
