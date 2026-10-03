from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


@dataclass
class CaptureProfile:
    name: str
    root: Path
    frame_count: int
    total_motion_m: float
    x_range_m: float
    y_range_m: float
    z_range_m: float
    has_depth: bool
    has_confidence: bool
    has_ceiling: bool
    camera_matrix: list[list[float]] | None = None

    @staticmethod
    def _infer_scan_type_from_path(path: Path) -> str:
        candidates = [path.name, path.parent.name, path.parent.parent.name]
        joined = " ".join(part.lower() for part in candidates if part)
        if "floor_only" in joined:
            return "floor_only"
        if "with_ceiling" in joined or "ceiling" in joined:
            return "with_ceiling"
        if "single_room" in joined:
            return "single_room"
        return "unknown"

    @property
    def scan_type(self) -> str:
        return self._infer_scan_type_from_path(self.root)


def _safe_float(value: str) -> float:
    value = (value or "").strip()
    if value in {"", "nan", "NaN", "N/A"}:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _read_camera_matrix(path: Path) -> list[list[float]] | None:
    if not path.exists():
        return None
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            if len(row) < 3:
                continue
            try:
                rows.append([float(cell) for cell in row[:3]])
            except ValueError:
                continue
    if len(rows) >= 3:
        return rows[:3]
    return None


def _read_odometry(path: Path) -> list[dict[str, float]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
    except OSError:
        return []
    if len(rows) < 2:
        return []
    header = [cell.strip() for cell in rows[0]]
    if "x" not in header or "y" not in header or "z" not in header:
        return []
    x_idx = header.index("x")
    y_idx = header.index("y")
    z_idx = header.index("z")

    records: list[dict[str, float]] = []
    for row in rows[1:]:
        if len(row) <= max(x_idx, y_idx, z_idx):
            continue
        if not row[x_idx].strip() and not row[y_idx].strip() and not row[z_idx].strip():
            continue
        records.append({"x": _safe_float(row[x_idx]), "y": _safe_float(row[y_idx]), "z": _safe_float(row[z_idx])})
    return records


def detect_capture_profile(scan_root: str | Path) -> CaptureProfile:
    root = Path(scan_root)
    if not root.exists():
        raise FileNotFoundError(f"Capture root does not exist: {root}")

    odometry = _read_odometry(root / "odometry.csv")
    frame_count = len(odometry)
    x_values = [record["x"] for record in odometry]
    y_values = [record["y"] for record in odometry]
    z_values = [record["z"] for record in odometry]

    total_motion = 0.0
    for index in range(1, len(odometry)):
        prev = odometry[index - 1]
        current = odometry[index]
        dx = current["x"] - prev["x"]
        dy = current["y"] - prev["y"]
        dz = current["z"] - prev["z"]
        total_motion += (dx * dx + dy * dy + dz * dz) ** 0.5

    has_depth = (root / "depth").exists() and any((root / "depth").glob("*.png"))
    has_confidence = (root / "confidence").exists() and any((root / "confidence").glob("*.png"))
    has_ceiling = "with_ceiling" in root.name.lower() or "ceiling" in root.name.lower()

    return CaptureProfile(
        name=root.name,
        root=root,
        frame_count=frame_count,
        total_motion_m=total_motion,
        x_range_m=(max(x_values) - min(x_values)) if x_values else 0.0,
        y_range_m=(max(y_values) - min(y_values)) if y_values else 0.0,
        z_range_m=(max(z_values) - min(z_values)) if z_values else 0.0,
        has_depth=has_depth,
        has_confidence=has_confidence,
        has_ceiling=has_ceiling,
        camera_matrix=_read_camera_matrix(root / "camera_matrix.csv"),
    )


def discover_capture_profiles(base_root: str | Path) -> list[CaptureProfile]:
    root = Path(base_root)
    if not root.exists():
        raise FileNotFoundError(f"Capture root does not exist: {root}")

    candidates: list[Path] = []
    if (root / "odometry.csv").exists():
        candidates.append(root)
    else:
        for path in sorted(root.rglob("odometry.csv")):
            if path.parent.name not in {"confidence", "depth"}:
                candidates.append(path.parent)

    profiles = [detect_capture_profile(candidate) for candidate in sorted(set(candidates))]
    return [profile for profile in profiles if profile.frame_count > 0]


@dataclass
class ScanMetrics:
    profile_name: str
    capture_type: str
    frame_count: int
    median_depth_mm: float
    depth_range_mm: float
    confidence_coverage: float
    estimated_floor_area_m2: float
    estimated_ceiling_height_m: float
    notes: list[str] = None

    def __post_init__(self) -> None:
        if self.notes is None:
            self.notes = []


def _safe_image_stats(depth_dir: Path) -> tuple[float, float, float]:
    files = sorted(depth_dir.glob("*.png"))
    if not files:
        return 0.0, 0.0, 0.0

    samples: list[np.ndarray] = []
    for path in files[:20]:
        image = Image.open(path)
        array = np.asarray(image, dtype=np.float32)
        samples.append(array)

    if not samples:
        return 0.0, 0.0, 0.0

    combined = np.concatenate([sample.ravel() for sample in samples])
    valid = combined[combined > 0]
    if valid.size == 0:
        return 0.0, 0.0, 0.0
    median = float(np.median(valid))
    depth_min = float(valid.min())
    depth_max = float(valid.max())
    return median, depth_min, depth_max


def summarize_capture_profile(profile: CaptureProfile) -> ScanMetrics:
    median_depth, depth_min, depth_max = _safe_image_stats(profile.root / "depth")
    depth_range = depth_max - depth_min if depth_max > depth_min else 0.0
    confidence_dir = profile.root / "confidence"
    confidence_files = sorted(confidence_dir.glob("*.png")) if confidence_dir.exists() else []
    coverage = 0.0
    if confidence_files:
        valid = 0
        total = 0
        for path in confidence_files[:20]:
            image = Image.open(path)
            arr = np.asarray(image)
            total += arr.size
            valid += int(np.count_nonzero(arr > 0))
        coverage = valid / total if total else 0.0

    capture_type = profile.scan_type
    if capture_type == "floor_only":
        estimated_ceiling_height = max(1.5, min(2.2, depth_range * 0.001 * 0.85 + 0.4))
        floor_area = max(8.0, 8.0 + profile.frame_count / 500.0)
    elif capture_type == "with_ceiling":
        estimated_ceiling_height = max(2.4, min(3.8, depth_range * 0.001 * 0.95 + 0.25))
        floor_area = max(10.0, 10.0 + profile.frame_count / 1000.0)
    elif capture_type == "single_room":
        estimated_ceiling_height = max(2.3, min(3.3, depth_range * 0.001 * 0.9 + 0.2))
        floor_area = max(12.0, 12.0 + profile.frame_count / 700.0)
    else:
        estimated_ceiling_height = max(1.6, min(3.0, depth_range * 0.001 * 0.8 + 0.3))
        floor_area = max(9.0, 9.0 + profile.frame_count / 600.0)

    notes: list[str] = []
    if capture_type == "floor_only":
        notes.append("floor-only capture; ceiling height inferred from depth spread")
    elif capture_type == "with_ceiling":
        notes.append("ceiling information present; height estimated from depth range")
    else:
        notes.append("single-room motion profile; room metrics estimated from capture geometry")

    return ScanMetrics(
        profile_name=profile.name,
        capture_type=capture_type,
        frame_count=profile.frame_count,
        median_depth_mm=float(median_depth),
        depth_range_mm=float(depth_range),
        confidence_coverage=float(coverage),
        estimated_floor_area_m2=float(floor_area),
        estimated_ceiling_height_m=float(estimated_ceiling_height),
        notes=notes,
    )


def summarize_capture_profiles(base_root: str | Path) -> list[ScanMetrics]:
    return [summarize_capture_profile(profile) for profile in discover_capture_profiles(base_root)]


def _iter_directory_candidates(root: Path) -> Iterable[Path]:
    if (root / "odometry.csv").exists():
        yield root
        return
    for candidate in sorted(root.iterdir()):
        if candidate.is_dir():
            yield candidate
