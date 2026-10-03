from __future__ import annotations

from pathlib import Path
from typing import Iterable

from property_scan.common.output_contract import Measurement, Opening, PropertyPlan, Room, confidence_interval_for_tier
from property_scan.data_loader import (
    discover_capture_profiles,
    confidence_quality_gate,
    estimate_projected_depth_geometry,
    estimate_pose_registered_depth_geometry,
    estimate_floor_plane_geometry,
    estimate_floor_aligned_footprint,
    estimate_wall_surface_geometry,
    estimate_ransac_floor_plane_geometry,
    estimate_translated_depth_geometry,
    summarize_capture_profile,
)

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


def _build_from_real_capture(property_root: Path, property_id: str) -> PropertyPlan | None:
    sessions = discover_capture_profiles(property_root)
    if not sessions:
        return None

    rooms: list[Room] = []
    for index, session in enumerate(sessions, start=1):
        scan_type = session.scan_type
        if scan_type == "floor_only":
            room_type = "bathroom"
        elif scan_type == "with_ceiling":
            room_type = "living room"
        elif scan_type == "single_room":
            room_type = "single_room"
        else:
            room_type = "hall"

        baseline = _ROOM_TYPE_BASELINES[_room_type_from_name(room_type)]
        metrics = summarize_capture_profile(session)
        confidence_quality = confidence_quality_gate(metrics.confidence_coverage)
        depth_geometry = estimate_projected_depth_geometry(session)
        translated_geometry = estimate_translated_depth_geometry(session)
        pose_registered_geometry = estimate_pose_registered_depth_geometry(session)
        floor_geometry = estimate_floor_plane_geometry(session)
        ransac_floor_geometry = estimate_ransac_floor_plane_geometry(session)
        footprint_geometry = estimate_floor_aligned_footprint(session)
        wall_geometry = estimate_wall_surface_geometry(session)
        area_m2 = round(metrics.estimated_floor_area_m2, 2)
        ceiling_height = round(metrics.estimated_ceiling_height_m, 2)

        wall_lengths = _estimate_wall_lengths(area_m2, baseline["aspect"])
        doors = [
            Opening(
                id=f"opening_{index}_door",
                type="door",
                width=Measurement(value=round(baseline["door_width"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_width"])),
                height=Measurement(value=round(baseline["door_height"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["door_height"])),
                location="south",
            )
        ]
        if session.frame_count > 3000:
            doors.append(
                Opening(
                    id=f"opening_{index}_window",
                    type="window",
                    width=Measurement(value=round(baseline["window_width"], 2), unit="m", confidence=confidence_interval_for_tier("photo", baseline["window_width"])),
                    height=Measurement(value=1.2, unit="m", confidence=confidence_interval_for_tier("photo", 1.2)),
                    location="north",
                )
            )

        rooms.append(
            Room(
                id=f"room_{index}",
                name=session.name.replace("_", " ").title(),
                floor_area=Measurement(value=area_m2, unit="m2", confidence=confidence_interval_for_tier("photo", area_m2)),
                ceiling_height=Measurement(value=ceiling_height, unit="m", confidence=confidence_interval_for_tier("photo", ceiling_height)),
                walls=[Measurement(value=value, unit="m", confidence=confidence_interval_for_tier("photo", value)) for value in wall_lengths],
                openings=doors,
                scope_items=[
                    {"item": "capture_geometry", "surface": "room", "quantity": float(session.frame_count), "unit": "frames"},
                    {"item": "scan_depth", "surface": "room", "quantity": 1.0 if session.has_depth else 0.0, "unit": "coverage"},
                    {"item": "confidence_coverage", "surface": "room", "quantity": round(metrics.confidence_coverage, 3), "unit": "ratio"},
                    {"item": "confidence_quality_gate", "surface": "room", "quantity": 1.0 if confidence_quality["passed"] else 0.0, "unit": "passed"},
                    {"item": "confidence_minimum_coverage", "surface": "room", "quantity": float(confidence_quality["minimum_coverage"]), "unit": "ratio"},
                    {"item": "depth_projected_x_extent", "surface": "room", "quantity": round(float(depth_geometry["x_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_projected_y_extent", "surface": "room", "quantity": round(float(depth_geometry["y_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_projected_z_extent", "surface": "room", "quantity": round(float(depth_geometry["z_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_projected_points", "surface": "room", "quantity": float(depth_geometry["projected_point_count"]), "unit": "points"},
                    {"item": "depth_translated_x_extent", "surface": "room", "quantity": round(float(translated_geometry["x_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_translated_y_extent", "surface": "room", "quantity": round(float(translated_geometry["y_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_translated_z_extent", "surface": "room", "quantity": round(float(translated_geometry["z_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_translated_points", "surface": "room", "quantity": float(translated_geometry["registered_point_count"]), "unit": "points"},
                    {"item": "depth_pose_registered_x_extent", "surface": "room", "quantity": round(float(pose_registered_geometry["x_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_pose_registered_y_extent", "surface": "room", "quantity": round(float(pose_registered_geometry["y_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_pose_registered_z_extent", "surface": "room", "quantity": round(float(pose_registered_geometry["z_extent_m"]), 3), "unit": "m"},
                    {"item": "depth_pose_registered_points", "surface": "room", "quantity": float(pose_registered_geometry["registered_point_count"]), "unit": "points"},
                    {"item": "floor_candidate_height", "surface": "room", "quantity": round(float(floor_geometry["floor_height_m"]), 3), "unit": "m"},
                    {"item": "floor_candidate_x_extent", "surface": "room", "quantity": round(float(floor_geometry["floor_x_extent_m"]), 3), "unit": "m"},
                    {"item": "floor_candidate_z_extent", "surface": "room", "quantity": round(float(floor_geometry["floor_z_extent_m"]), 3), "unit": "m"},
                    {"item": "floor_candidate_inliers", "surface": "room", "quantity": float(floor_geometry["floor_inlier_count"]), "unit": "points"},
                    {"item": "ransac_floor_height", "surface": "room", "quantity": round(float(ransac_floor_geometry["floor_height_m"]), 3), "unit": "m"},
                    {"item": "ransac_floor_x_extent", "surface": "room", "quantity": round(float(ransac_floor_geometry["floor_x_extent_m"]), 3), "unit": "m"},
                    {"item": "ransac_floor_z_extent", "surface": "room", "quantity": round(float(ransac_floor_geometry["floor_z_extent_m"]), 3), "unit": "m"},
                    {"item": "ransac_floor_inliers", "surface": "room", "quantity": float(ransac_floor_geometry["floor_inlier_count"]), "unit": "points"},
                    {"item": "ransac_floor_inlier_ratio", "surface": "room", "quantity": round(float(ransac_floor_geometry["floor_inlier_ratio"]), 3), "unit": "ratio"},
                    {"item": "floor_footprint_area", "surface": "room", "quantity": float(footprint_geometry["footprint_area_m2"]), "unit": "m2"},
                    {"item": "floor_footprint_points", "surface": "room", "quantity": float(footprint_geometry["footprint_point_count"]), "unit": "points"},
                    {"item": "wall_surface_points", "surface": "walls", "quantity": float(wall_geometry["wall_point_count"]), "unit": "points"},
                    {"item": "wall_surface_vertical_extent", "surface": "walls", "quantity": round(float(wall_geometry["wall_vertical_extent_m"]), 3), "unit": "m"},
                    {"item": "wall_surface_u_extent", "surface": "walls", "quantity": round(float(wall_geometry["wall_horizontal_u_extent_m"]), 3), "unit": "m"},
                    {"item": "wall_surface_v_extent", "surface": "walls", "quantity": round(float(wall_geometry["wall_horizontal_v_extent_m"]), 3), "unit": "m"},
                ],
                adjacency=[],
            )
        )

    connections = []
    for idx in range(1, len(rooms)):
        connections.append({"from": f"room_{idx}", "to": f"room_{idx + 1}", "type": "hallway"})
    return PropertyPlan(capture_tier="photo", property_id=property_id, rooms=rooms, whole_property_connections=connections)


def build_photo_plan(property_root: str | Path, property_id: str = "property") -> PropertyPlan:
    root = Path(property_root)
    real_plan = _build_from_real_capture(root, property_id)
    if real_plan is not None:
        return real_plan

    rooms: list[Room] = []
    room_dirs = list(_iter_room_dirs(root))
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
