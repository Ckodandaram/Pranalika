from __future__ import annotations

from pathlib import Path
from typing import Iterable

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier


def _iter_room_dirs(property_root: str | Path) -> Iterable[Path]:
    root = Path(property_root)
    if not root.exists():
        raise FileNotFoundError(f"Property root does not exist: {root}")
    return sorted([p for p in root.iterdir() if p.is_dir()])


def build_photo_plan(property_root: str | Path, property_id: str = "property") -> PropertyPlan:
    rooms: list[Room] = []
    for index, room_dir in enumerate(_iter_room_dirs(property_root), start=1):
        image_count = len(list(room_dir.glob("*.*")))
        nominal_area = 12.0 + max(0, image_count - 2) * 1.5
        room = Room(
            id=f"room_{index}",
            name=room_dir.name.replace("_", " ").title(),
            floor_area=Measurement(value=nominal_area, unit="m2", confidence=confidence_interval_for_tier("photo", nominal_area)),
            ceiling_height=Measurement(value=2.70, unit="m", confidence=confidence_interval_for_tier("photo", 2.70)),
            walls=[
                Measurement(value=3.4, unit="m", confidence=confidence_interval_for_tier("photo", 3.4)),
                Measurement(value=4.1, unit="m", confidence=confidence_interval_for_tier("photo", 4.1)),
                Measurement(value=3.4, unit="m", confidence=confidence_interval_for_tier("photo", 3.4)),
                Measurement(value=4.1, unit="m", confidence=confidence_interval_for_tier("photo", 4.1)),
            ],
            openings=[
                Opening(
                    id=f"opening_{index}_door",
                    type="door",
                    width=Measurement(value=0.90, unit="m", confidence=confidence_interval_for_tier("photo", 0.90)),
                    height=Measurement(value=2.10, unit="m", confidence=confidence_interval_for_tier("photo", 2.10)),
                    location="south",
                )
            ],
            scope_items=[
                {"item": "paint_retouch", "surface": "wall", "quantity": 1.0, "unit": "room"},
            ],
            adjacency=[],
        )
        rooms.append(room)

    connections = [
        {"from": "room_1", "to": "room_2", "type": "hallway"},
    ] if len(rooms) > 1 else []
    return PropertyPlan(capture_tier="photo", property_id=property_id, rooms=rooms, whole_property_connections=connections)
