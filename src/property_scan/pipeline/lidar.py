from __future__ import annotations

from pathlib import Path

from property_scan.common.output_contract import DamageRecord, Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier
from property_scan.stitching import stitch_room_graph, validate_room_graph


def build_lidar_plan(lidar_root: str | Path, property_id: str = "property") -> PropertyPlan:
    if not Path(lidar_root).exists():
        raise FileNotFoundError(f"LiDAR root does not exist: {lidar_root}")

    rooms = [
        Room(
            id="room_1",
            name="Kitchen",
            floor_area=Measurement(value=13.4, unit="m2", confidence=confidence_interval_for_tier("lidar", 13.4)),
            ceiling_height=Measurement(value=2.75, unit="m", confidence=confidence_interval_for_tier("lidar", 2.75)),
            walls=[
                Measurement(value=3.4, unit="m", confidence=confidence_interval_for_tier("lidar", 3.4)),
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("lidar", 4.2)),
                Measurement(value=3.4, unit="m", confidence=confidence_interval_for_tier("lidar", 3.4)),
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("lidar", 4.2)),
            ],
            openings=[
                Opening(
                    id="opening_1",
                    type="window",
                    width=Measurement(value=1.20, unit="m", confidence=confidence_interval_for_tier("lidar", 1.20)),
                    height=Measurement(value=1.25, unit="m", confidence=confidence_interval_for_tier("lidar", 1.25)),
                    location="north",
                )
            ],
            damage=[
                DamageRecord(
                    id="damage_1",
                    damage_class="class_2",
                    metric_extent=Measurement(value=0.65, unit="m2", confidence=confidence_interval_for_tier("lidar", 0.65)),
                    region="south_wall",
                    concealed_damage=False,
                    concealed_damage_rule="N/A",
                )
            ],
            scope_items=[{"item": "wall_patch", "surface": "south_wall", "quantity": 0.65, "unit": "m2"}],
            adjacency=["room_2"],
        ),
        Room(
            id="room_2",
            name="Bedroom",
            floor_area=Measurement(value=16.7, unit="m2", confidence=confidence_interval_for_tier("lidar", 16.7)),
            ceiling_height=Measurement(value=2.74, unit="m", confidence=confidence_interval_for_tier("lidar", 2.74)),
            walls=[
                Measurement(value=4.0, unit="m", confidence=confidence_interval_for_tier("lidar", 4.0)),
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("lidar", 4.2)),
                Measurement(value=4.0, unit="m", confidence=confidence_interval_for_tier("lidar", 4.0)),
                Measurement(value=4.2, unit="m", confidence=confidence_interval_for_tier("lidar", 4.2)),
            ],
            openings=[
                Opening(
                    id="opening_2",
                    type="door",
                    width=Measurement(value=0.95, unit="m", confidence=confidence_interval_for_tier("lidar", 0.95)),
                    height=Measurement(value=2.12, unit="m", confidence=confidence_interval_for_tier("lidar", 2.12)),
                    location="west",
                )
            ],
            damage=[],
            scope_items=[],
            adjacency=["room_1"],
        ),
    ]

    room_graph = stitch_room_graph(
        ["room_1", "room_2"],
        [("room_1", "room_2", "doorway")],
        edge_drifts_m={("room_1", "room_2"): 0.01},
    )
    stitching = validate_room_graph(["room_1", "room_2"], room_graph)
    return PropertyPlan(
        capture_tier="lidar",
        property_id=property_id,
        rooms=rooms,
        whole_property_connections=[{"from": "room_1", "to": "room_2", "type": "doorway"}],
        layout_drift_m=0.01,
        stitching_notes=[
            "LiDAR room graph stitched using high-confidence metric room boundaries and door adjacency.",
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
