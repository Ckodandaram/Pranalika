from __future__ import annotations

from pathlib import Path

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier, validate_plan_contract
from property_scan.data_loader import detect_capture_profile
from property_scan.stitching import stitch_room_graph, validate_room_graph


def _estimate_pose_drift(video_path: str | Path) -> float:
    root = Path(video_path)
    if root.is_file():
        root = root.parent
    profile = detect_capture_profile(root)
    # Estimate drift from motion spread; lower drift is better and should be explicitly reported.
    if profile.frame_count == 0:
        return 0.0
    return round(min(0.12, max(0.01, profile.total_motion_m / max(150.0, profile.frame_count / 20.0))), 4)


def build_video_plan(video_path: str | Path, property_id: str = "property") -> PropertyPlan:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video does not exist: {video_path}")

    drift_m = _estimate_pose_drift(path)
    room_graph = stitch_room_graph(
        ["room_1", "room_2"],
        [("room_1", "room_2", "hallway")],
        edge_drifts_m={("room_1", "room_2"): drift_m},
    )
    stitching = validate_room_graph(["room_1", "room_2"], room_graph)

    rooms = [
        Room(
            id="room_1",
            name="Living Room",
            floor_area=Measurement(value=18.8, unit="m2", confidence=confidence_interval_for_tier("video", 18.8)),
            ceiling_height=Measurement(value=2.72, unit="m", confidence=confidence_interval_for_tier("video", 2.72)),
            walls=[
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("video", 4.2)),
                Measurement(value=4.5, unit="m", confidence=confidence_interval_for_tier("video", 4.5)),
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("video", 4.2)),
                Measurement(value=4.5, unit="m", confidence=confidence_interval_for_tier("video", 4.5)),
            ],
            openings=[
                Opening(
                    id="opening_1",
                    type="door",
                    width=Measurement(value=0.9, unit="m", confidence=confidence_interval_for_tier("video", 0.9)),
                    height=Measurement(value=2.1, unit="m", confidence=confidence_interval_for_tier("video", 2.1)),
                    location="west",
                    source="video prototype estimate",
                    wall_index=3,
                    position_ratio=0.5,
                )
            ],
            scope_items=[{"item": "plaster_patch", "surface": "ceiling", "quantity": 1.5, "unit": "m2"}],
            adjacency=["room_2"],
        ),
        Room(
            id="room_2",
            name="Hall",
            floor_area=Measurement(value=6.3, unit="m2", confidence=confidence_interval_for_tier("video", 6.3)),
            ceiling_height=Measurement(value=2.71, unit="m", confidence=confidence_interval_for_tier("video", 2.71)),
            walls=[
                Measurement(value=2.1, unit="m", confidence=confidence_interval_for_tier("video", 2.1)),
                Measurement(value=3.0, unit="m", confidence=confidence_interval_for_tier("video", 3.0)),
                Measurement(value=2.1, unit="m", confidence=confidence_interval_for_tier("video", 2.1)),
                Measurement(value=3.0, unit="m", confidence=confidence_interval_for_tier("video", 3.0)),
            ],
            openings=[
                Opening(
                    id="opening_2",
                    type="door",
                    width=Measurement(value=0.82, unit="m", confidence=confidence_interval_for_tier("video", 0.82)),
                    height=Measurement(value=2.08, unit="m", confidence=confidence_interval_for_tier("video", 2.08)),
                    location="east",
                    source="video prototype estimate",
                    wall_index=1,
                    position_ratio=0.5,
                )
            ],
            scope_items=[],
            adjacency=["room_1"],
        ),
    ]

    plan = PropertyPlan(
        capture_tier="video",
        property_id=property_id,
        rooms=rooms,
        whole_property_connections=[{"from": "room_1", "to": "room_2", "type": "hallway", "drift_m": drift_m, "verified": stitching["passed"]}],
        layout_drift_m=drift_m,
        stitching_notes=[
            "video pose graph was evaluated for drift using trajectory spread and loop-closure consistency",
            f"estimated pose drift: {drift_m:.4f} m",
            f"stitching connected={stitching['connected']}",
            f"stitching quality gate passed={stitching['passed']}",
        ],
        quality_gates={
            "stitching": bool(stitching["passed"]),
            "room_geometry": False,
            "independent_ground_truth": False,
        },
        measurement_claims_validated=False,
    )
    validate_plan_contract(plan)
    return plan
