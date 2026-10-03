from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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

    @property
    def scan_type(self) -> str:
        lower = self.name.lower()
        if "floor_only" in lower:
            return "floor_only"
        if "with_ceiling" in lower or "ceiling" in lower:
            return "with_ceiling"
        if "single_room" in lower:
            return "single_room"
        return "unknown"


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


def _iter_directory_candidates(root: Path) -> Iterable[Path]:
    if (root / "odometry.csv").exists():
        yield root
        return
    for candidate in sorted(root.iterdir()):
        if candidate.is_dir():
            yield candidate
