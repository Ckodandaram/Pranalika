from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path


def _axis_angle_to_matrix(rx: float, ry: float, rz: float) -> tuple[tuple[float, ...], ...]:
    angle = math.sqrt(rx * rx + ry * ry + rz * rz)
    if angle < 1e-12:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    x, y, z = rx / angle, ry / angle, rz / angle
    cosine = math.cos(angle)
    sine = math.sin(angle)
    one_minus_cosine = 1.0 - cosine
    return (
        (
            cosine + x * x * one_minus_cosine,
            x * y * one_minus_cosine - z * sine,
            x * z * one_minus_cosine + y * sine,
        ),
        (
            y * x * one_minus_cosine + z * sine,
            cosine + y * y * one_minus_cosine,
            y * z * one_minus_cosine - x * sine,
        ),
        (
            z * x * one_minus_cosine - y * sine,
            z * y * one_minus_cosine + x * sine,
            cosine + z * z * one_minus_cosine,
        ),
    )


def _world_to_camera_to_camera_to_world(
    rotation: tuple[tuple[float, ...], ...],
    translation: tuple[float, float, float],
) -> tuple[tuple[float, float, float, float], tuple[float, float, float]]:
    inverse_translation = tuple(
        -sum(rotation[row][column] * translation[row] for row in range(3))
        for column in range(3)
    )
    inverse_rotation = tuple(
        tuple(rotation[column][row] for column in range(3))
        for row in range(3)
    )
    # ARKitScenes uses Z as the upright axis. Pranalika uses Y-up and a
    # right-handed X/Y/Z frame, so map (x, y, z) to (x, z, -y).
    axis_map = (
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, -1.0, 0.0),
    )
    mapped_rotation = tuple(
        tuple(
            sum(axis_map[row][inner] * inverse_rotation[inner][outer] * axis_map[column][outer] for inner in range(3) for outer in range(3))
            for column in range(3)
        )
        for row in range(3)
    )
    mapped_translation = tuple(
        sum(axis_map[row][column] * inverse_translation[column] for column in range(3))
        for row in range(3)
    )
    trace = sum(mapped_rotation[index][index] for index in range(3))
    qw = math.sqrt(max(0.0, 1.0 + trace)) * 0.5
    divisor = max(4.0 * qw, 1e-12)
    qx = (mapped_rotation[2][1] - mapped_rotation[1][2]) / divisor
    qy = (mapped_rotation[0][2] - mapped_rotation[2][0]) / divisor
    qz = (mapped_rotation[1][0] - mapped_rotation[0][1]) / divisor
    return (qx, qy, qz, qw), mapped_translation


def _read_traj(path: Path) -> list[tuple[float, tuple[float, float, float, float], tuple[float, float, float]]]:
    poses = []
    for line in path.read_text(encoding="utf-8").splitlines():
        values = line.split()
        if len(values) < 7:
            continue
        timestamp, rx, ry, rz, tx, ty, tz = map(float, values[:7])
        rotation = _axis_angle_to_matrix(rx, ry, rz)
        quaternion, translation = _world_to_camera_to_camera_to_world(rotation, (tx, ty, tz))
        poses.append((timestamp, quaternion, translation))
    if not poses:
        raise ValueError(f"ARKitScenes trajectory contains no valid poses: {path}")
    return poses


def _pincam_to_matrix(path: Path) -> list[list[float]]:
    values = [float(value) for value in path.read_text(encoding="utf-8").split()]
    if len(values) < 6:
        raise ValueError(f"ARKitScenes intrinsics file is incomplete: {path}")
    _, _, fx, fy, cx, cy = values[:6]
    return [[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]]


def convert_capture(
    capture_root: str | Path,
    output_root: str | Path,
    *,
    copy_frames: bool = True,
) -> Path:
    """Convert one raw ARKitScenes capture to Pranalika's normalized layout."""
    source = Path(capture_root)
    destination = Path(output_root)
    depth_dir = source / "lowres_depth"
    confidence_dir = source / "confidence"
    trajectory_path = source / "lowres_wide.traj"
    intrinsics_dir = source / "lowres_wide_intrinsics"
    if not depth_dir.is_dir() or not trajectory_path.is_file() or not intrinsics_dir.is_dir():
        raise FileNotFoundError(
            "ARKitScenes capture requires lowres_depth, lowres_wide.traj, and "
            f"lowres_wide_intrinsics: {source}"
        )

    depth_files = sorted(depth_dir.glob("*.png"))
    if not depth_files:
        raise ValueError(f"ARKitScenes capture contains no depth frames: {depth_dir}")
    poses = _read_traj(trajectory_path)
    intrinsics_files = sorted(intrinsics_dir.glob("*.pincam"))
    if not intrinsics_files:
        raise ValueError(f"ARKitScenes capture contains no intrinsics files: {intrinsics_dir}")

    (destination / "depth").mkdir(parents=True, exist_ok=True)
    (destination / "confidence").mkdir(parents=True, exist_ok=True)
    shutil.copy2(intrinsics_files[0], destination / "arkitscenes_intrinsics.pincam")
    mesh_files = sorted(source.glob("*_3dod_mesh.ply"))
    if mesh_files:
        shutil.copy2(mesh_files[0], destination / "arkitscenes_mesh.ply")
    matrix = _pincam_to_matrix(intrinsics_files[0])
    with (destination / "camera_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(matrix)

    with (destination / "odometry.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame", "x", "y", "z", "qx", "qy", "qz", "qw"])
        for depth_file in depth_files:
            timestamp = float(depth_file.stem.rsplit("_", 1)[-1])
            pose = min(poses, key=lambda item: abs(item[0] - timestamp))
            _, quaternion, translation = pose
            writer.writerow([depth_file.stem, *translation, *quaternion])
            if copy_frames:
                shutil.copy2(depth_file, destination / "depth" / depth_file.name)
                confidence_file = confidence_dir / depth_file.name
                if confidence_file.exists():
                    shutil.copy2(confidence_file, destination / "confidence" / confidence_file.name)

    return destination
