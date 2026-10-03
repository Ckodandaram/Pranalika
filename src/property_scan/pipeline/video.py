from __future__ import annotations

from pathlib import Path

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier


def build_video_plan(video_path: str | Path, property_id: str = "property") -> PropertyPlan:
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video does not exist: {video_path}")

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
                )
            ],
            scope_items=[],
            adjacency=["room_1"],
        ),
    ]

    return PropertyPlan(capture_tier="video", property_id=property_id, rooms=rooms, whole_property_connections=[{"from": "room_1", "to": "room_2", "type": "hallway"}])
