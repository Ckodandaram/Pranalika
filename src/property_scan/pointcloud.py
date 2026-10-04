from __future__ import annotations

from pathlib import Path

import numpy as np


def load_point_cloud(root: str | Path) -> np.ndarray:
    """Load a metric XYZ point cloud from common interchange formats."""
    path = Path(root)
    if path.is_dir():
        candidates = [
            *path.glob("*.ply"),
            *path.glob("*.pcd"),
            *path.glob("*.xyz"),
            *path.glob("*.pts"),
            *path.glob("*.csv"),
            *path.glob("*.npy"),
            *path.glob("*.npz"),
        ]
        if not candidates:
            raise FileNotFoundError(f"no point-cloud file found under {path}")
        path = candidates[0]
    suffix = path.suffix.lower()
    if suffix == ".npy":
        points = np.asarray(np.load(path), dtype=float)
    elif suffix == ".npz":
        archive = np.load(path)
        key = "points" if "points" in archive else archive.files[0]
        points = np.asarray(archive[key], dtype=float)
    elif suffix == ".ply":
        points = _load_ply(path)
    elif suffix == ".pcd":
        points = _load_pcd(path)
    else:
        points = _load_delimited(path)
    if points.ndim != 2 or points.shape[1] < 3:
        raise ValueError(f"point cloud must have at least three columns: {path}")
    points = points[:, :3]
    points = points[np.isfinite(points).all(axis=1)]
    if len(points) < 20:
        raise ValueError(f"point cloud has too few valid points: {path}")
    return points


def _load_delimited(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            values = line.replace(",", " ").split()
            if len(values) < 3:
                continue
            try:
                rows.append([float(value) for value in values[:3]])
            except ValueError:
                continue
    return np.asarray(rows, dtype=float)


def _load_pcd(path: Path) -> np.ndarray:
    header: list[str] = []
    with path.open("rb") as handle:
        while True:
            line = handle.readline()
            if not line:
                raise ValueError(f"PCD header is incomplete: {path}")
            text = line.decode("ascii", errors="replace").strip()
            header.append(text)
            if text.lower() == "data ascii":
                return _load_delimited_from_handle(handle)
            if text.lower().startswith("data binary"):
                break
        fields = _header_values(header, "fields")
        sizes = [int(value) for value in _header_values(header, "size")]
        types = _header_values(header, "type")
        counts = [int(value) for value in _header_values(header, "count")] or [1] * len(fields)
        points_count = int((_header_values(header, "points") or ["0"])[0])
        if not fields or points_count <= 0:
            raise ValueError(f"PCD binary header is invalid: {path}")
        dtype_fields = []
        for field, size, kind, count in zip(fields, sizes, types, counts):
            dtype_kind = {"F": "f", "U": "u", "I": "i"}.get(kind)
            if dtype_kind is None:
                raise ValueError(f"unsupported PCD field type: {kind}")
            dtype_fields.append((field, f"<{dtype_kind}{size}", (count,)))
        data = np.frombuffer(handle.read(), dtype=np.dtype(dtype_fields), count=points_count)
        return np.column_stack([data[name][:, 0] for name in ("x", "y", "z")])


def _load_delimited_from_handle(handle) -> np.ndarray:
    rows = []
    for raw in handle:
        values = raw.decode("ascii", errors="replace").replace(",", " ").split()
        if len(values) >= 3:
            rows.append([float(value) for value in values[:3]])
    return np.asarray(rows, dtype=float)


def _header_values(header: list[str], key: str) -> list[str]:
    for line in header:
        parts = line.split()
        if parts and parts[0].lower() == key:
            return parts[1:]
    return []


def _load_ply(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        header: list[str] = []
        while True:
            line = handle.readline()
            if not line:
                raise ValueError(f"PLY header is incomplete: {path}")
            text = line.decode("ascii", errors="replace").strip()
            header.append(text)
            if text == "end_header":
                break
        vertex_line = next((line for line in header if line.startswith("element vertex ")), None)
        if vertex_line is None:
            raise ValueError(f"PLY has no vertex element: {path}")
        count = int(vertex_line.split()[-1])
        format_line = next(line for line in header if line.startswith("format "))
        if "ascii" in format_line:
            return _load_delimited_from_handle(handle)[:count]
        if "binary_little_endian" not in format_line:
            raise ValueError(f"unsupported PLY format: {format_line}")
        properties = [line.split() for line in header if line.startswith("property ") and not line.startswith("property list")]
        dtype = []
        mapping = {"float": "f4", "float32": "f4", "double": "f8", "uchar": "u1", "uint8": "u1"}
        for property_parts in properties:
            if len(property_parts) != 3 or property_parts[1] not in mapping:
                raise ValueError(f"unsupported PLY vertex property: {' '.join(property_parts)}")
            dtype.append((property_parts[2], mapping[property_parts[1]]))
        data = np.frombuffer(handle.read(), dtype=np.dtype(dtype), count=count)
        return np.column_stack([data[name] for name in ("x", "y", "z")])


def reconstruct_lidar_geometry(points: np.ndarray) -> dict[str, object]:
    """Extract metric room evidence from a registered XYZ cloud."""
    lower = np.percentile(points[:, 1], 2)
    upper = np.percentile(points[:, 1], 98)
    floor_band = points[np.abs(points[:, 1] - lower) <= max(0.03, (upper - lower) * 0.02)]
    floor_band = floor_band if len(floor_band) >= 10 else points
    x_min, x_max = np.percentile(floor_band[:, 0], [2, 98])
    z_min, z_max = np.percentile(floor_band[:, 2], [2, 98])
    width = float(max(x_max - x_min, 0.01))
    length = float(max(z_max - z_min, 0.01))
    height = float(max(upper - lower, 0.01))
    return {
        "floor_area_m2": width * length,
        "wall_lengths_m": [width, length, width, length],
        "ceiling_height_m": height,
        "floor_inlier_count": int(len(floor_band)),
        "point_count": int(len(points)),
        "bounds_m": {"x": [float(x_min), float(x_max)], "y": [float(lower), float(upper)], "z": [float(z_min), float(z_max)]},
    }
