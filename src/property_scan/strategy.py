from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StackComponent:
    name: str
    source_repo: str
    role: str
    why_it_matters: str


def selected_stack() -> List[StackComponent]:
    return [
        StackComponent(
            name="Room-Reconstruction-Demo",
            source_repo="Room-Reconstruction-Demo-main",
            role="Photo tier reconstruction baseline",
            why_it_matters="Uses multi-view room photos, depth estimation, and COLMAP-style registration to produce a 3D room proxy and floor-plan output from minimal camera input.",
        ),
        StackComponent(
            name="RoomPlanDemo",
            source_repo="RoomPlanDemo-main",
            role="LiDAR tier capture and room geometry reference",
            why_it_matters="Demonstrates Apple RoomPlan capture, geometry extraction, and a polished 2D floor-plan editor for LiDAR-capable iPhones and iPads.",
        ),
        StackComponent(
            name="openPlan3D",
            source_repo="openPlan3D-main",
            role="Common floor-plan editor and room stitching surface",
            why_it_matters="Provides a browser-native 2D/3D floor-plan editor, room-boundary tooling, and RoomPlan import examples that align with the assignment's whole-property output contract.",
        ),
        StackComponent(
            name="COLMAP",
            source_repo="colmap-main",
            role="Photogrammetry and pose estimation backbone",
            why_it_matters="Handles feature extraction, multi-view matching, and sparse reconstruction required for photo/video camera pose estimation before room stitching.",
        ),
    ]


def pipeline_selection() -> Dict[str, str]:
    return {
        "photo": "Room-Reconstruction-Demo + COLMAP + dense reconstruction",
        "video": "COLMAP / SLAM pose estimation + multi-room drift correction + same output contract",
        "lidar": "RoomPlanDemo / Apple RoomPlan + room-level floor-plan extraction",
        "whole_property": "openPlan3D room graph stitching + room adjacency and plan layout",
    }
