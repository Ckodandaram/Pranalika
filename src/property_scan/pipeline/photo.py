from __future__ import annotations

from pathlib import Path
from typing import Iterable

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
_ROOM_TYPE_BASELINES = {
    "living room": {"area": 18.5, "ceiling": 2.72, "aspect": 1.35, "door_width": 0.90, "door_height": 2.08, "window_width": 1.20},
    "bedroom": {"area": 13.8, "ceiling": 2.70, "aspect": 1.20, "door_width": 0.88, "door_height": 2.04, "window_width": 1.10},
    "kitchen": {"area": 11.5, "ceiling": 2.75, "aspect": 1.10, "door_width": 0.82, "door_height": 2.02, "window_width": 1.40},
    "bathroom": {"area": 6.8, "ceiling": 2.60, "aspect": 1.00, "door_width": 0.72, "door_height": 2.00, "window_width": 0.80},
    "hall": {"area": 7.5, "ceiling": 2.72, "aspect": 1.65, "door_width": 0.90, "door_height": 2.08, "window_width": 0.90},
    "default": {"area": 12.0, "ceiling": 2.70, "aspect": 1.25, "door_width": 0.85, "door_height": 2.05, "window_width": 1.00},
}


def _iter_room_dirs(property_root: str | Path) -> Iterable[Path]:
    root = Path(property_root)
    if not root.exists():
        raise FileNotFoundError(f"Property root does not exist: {root}")
    return sorted([p for p in root.iterdir() if p.is_dir()])


def _room_type_from_name(room_name: str) -> str:
    lower_name = room_name.lower().replace("_", " ")
    for key in _ROOM_TYPE_BASELINES:
        if key != "default" and key in lower_name:
            return key
    return "default"


def _image_count_for_room(room_dir: Path) -> int:
    return sum(1 for p in room_dir.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_SUFFIXES)


def _estimate_wall_lengths(area_m2: float, aspect_ratio: float) -> list[float]:
    width = (area_m2 / aspect_ratio) ** 0.5
    depth = area_m2 / width
    return [round(width, 2), round(depth, 2), round(width, 2), round(depth, 2)]


def _estimate_openings(room_dir: Path, room_type: str, image_count: int) -> list[Opening]:
    baseline = _ROOM_TYPE_BASELINES[room_type]
    door_count = 1 if image_count >= 2 else 0
    window_count = 1 if image_count >= 3 else 0

    openings: list[Opening] = []
    for idx in range(door_count):
        openings.append(
            Opening(
                id=f"opening_{room_dir.name}_{idx + 1}_door",
                type="door",
                width=Measurement(value=round(baseline["door_width"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_width"])),
                height=Measurement(value=round(baseline["door_height"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_height"])),
                location="south" if idx == 0 else "east",
            )
        )
    for idx in range(window_count):
        openings.append(
            Opening(
                id=f"opening_{room_dir.name}_{idx + 1}_window",
                type="window",
                width=Measurement(value=round(baseline["window_width"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["window_width"])),
                height=Measurement(value=1.15, unit="m", confidence=confidence_interval_for_tier("photo", 1.15)),
                location="north" if idx == 0 else "west",
            )
        )
    if not openings and image_count > 0:
        openings.append(
            Opening(
                id=f"opening_{room_dir.name}_1_door",
                type="door",
                width=Measurement(value=round(baseline["door_width"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_width"])),
                height=Measurement(value=round(baseline["door_height"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_height"])),
                location="south",
            )
        )
    return openings


def _infer_room_metrics(room_dir: Path, room_index: int) -> tuple[float, float, list[float], list[Opening]]:
    room_type = _room_type_from_name(room_dir.name)
    baseline = _ROOM_TYPE_BASELINES[room_type]
    image_count = _image_count_for_room(room_dir)
    area_multiplier = 1.0 + max(0, image_count - 2) * 0.05
    area_m2 = round(baseline["area"] * area_multiplier, 2)
    wall_lengths = _estimate_wall_lengths(area_m2, baseline["aspect"])
    openings = _estimate_openings(room_dir, room_type, image_count)
    ceiling_height = round(baseline["ceiling"], 2)
    if image_count <= 1:
        ceiling_height = round(ceiling_height - 0.04, 2)
    return area_m2, ceiling_height, wall_lengths, openings


def build_photo_plan(property_root: str | Path, property_id: str = "property") -> PropertyPlan:
    rooms: list[Room] = []
    room_dirs = list(_iter_room_dirs(property_root))
    for index, room_dir in enumerate(room_dirs, start=1):
        room_type = _room_type_from_name(room_dir.name)
        image_count = _image_count_for_room(room_dir)
        area_m2, ceiling_height, wall_lengths, openings = _infer_room_metrics(room_dir, index)
        room = Room(
            id=f"room_{index}",
            name=room_dir.name.replace("_", " ").title(),
            floor_area=Measurement(value=area_m2, unit="m2", confidence=confidence_interval_for_tier("photo", area_m2)),
            ceiling_height=Measurement(value=ceiling_height, unit="m", confidence=confidence_interval_for_tier("photo", ceiling_height)),
            walls=[Measurement(value=value, unit="m", confidence=confidence_interval_for_tier("photo", value)) for value in wall_lengths],
            openings=openings,
            scope_items=[
                {"item": "capture_review", "surface": "room", "quantity": float(max(1, image_count)), "unit": "images"},
            ],
            adjacency=[],
        )
        rooms.append(room)

    connections = []
    for idx in range(1, len(rooms)):
        connections.append({"from": f"room_{idx}", "to": f"room_{idx + 1}", "type": "hallway"})
    return PropertyPlan(capture_tier="photo", property_id=property_id, rooms=rooms, whole_property_connections=connections)
