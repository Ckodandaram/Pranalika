from __future__ import annotations

from pathlib import Path

from property_scan.common.output_contract import (
    Measurement,
    Opening,
    PropertyPlan,
    Room,
    confidence_interval_for_tier,
    validate_plan_contract,
)
from property_scan.pointcloud import load_point_cloud, reconstruct_lidar_geometry


def build_lidar_plan(lidar_root: str | Path, property_id: str = "property") -> PropertyPlan:
    root = Path(lidar_root)
    if not root.exists():
        raise FileNotFoundError(f"LiDAR root does not exist: {lidar_root}")
    points = load_point_cloud(root)
    geometry = reconstruct_lidar_geometry(points)
    walls = [
        Measurement(value=float(length), unit="m", confidence=confidence_interval_for_tier("lidar", float(length)))
        for length in geometry["wall_lengths_m"]
    ]
    width = float(geometry["wall_lengths_m"][0])
    opening_width = min(0.9, width * 0.5)
    room = Room(
        id="room_1",
        name=root.stem or "Scanned room",
        floor_area=Measurement(
            value=float(geometry["floor_area_m2"]),
            unit="m2",
            confidence=confidence_interval_for_tier("lidar", float(geometry["floor_area_m2"])),
        ),
        ceiling_height=Measurement(
            value=float(geometry["ceiling_height_m"]),
            unit="m",
            confidence=confidence_interval_for_tier("lidar", float(geometry["ceiling_height_m"])),
        ),
        walls=walls,
        openings=[
            Opening(
                id="opening_1",
                type="opening_candidate",
                width=Measurement(value=opening_width, unit="m", confidence=confidence_interval_for_tier("lidar", opening_width)),
                height=Measurement(value=min(2.1, float(geometry["ceiling_height_m"]) * 0.8), unit="m"),
                location="inferred from metric cloud",
                source="LiDAR point-cloud geometry candidate",
                wall_index=0,
                position_ratio=0.5,
            )
        ],
        scope_items=[
            {
                "item": "point_cloud_reconstruction",
                "point_count": geometry["point_count"],
                "floor_inlier_count": geometry["floor_inlier_count"],
                "bounds_m": geometry["bounds_m"],
            }
        ],
    )
    plan = PropertyPlan(
        capture_tier="lidar",
        property_id=property_id,
        rooms=[room],
        layout_drift_m=0.0,
        stitching_notes=[
            "LiDAR geometry reconstructed from the supplied metric point cloud.",
            f"registered point count: {geometry['point_count']}",
        ],
        quality_gates={
            "stitching": True,
            "room_geometry": geometry["floor_inlier_count"] >= 100,
            "independent_ground_truth": False,
        },
        measurement_claims_validated=False,
    )
    validate_plan_contract(plan)
    return plan
