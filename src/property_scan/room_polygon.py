from __future__ import annotations

from math import atan2
from typing import Iterable, Sequence

Point = tuple[float, float]
Segment = tuple[Point, Point]


def _distance(first: Point, second: Point) -> float:
    return ((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2) ** 0.5


def _snap_points(segments: Sequence[Segment], tolerance_m: float) -> tuple[list[Segment], int]:
    representatives: list[Point] = []
    snapped: list[Segment] = []
    for start, end in segments:
        snapped_segment: list[Point] = []
        for point in (start, end):
            match = next(
                (index for index, representative in enumerate(representatives)
                 if _distance(point, representative) <= tolerance_m),
                None,
            )
            if match is None:
                representatives.append(point)
                snapped_segment.append(point)
            else:
                snapped_segment.append(representatives[match])
        if _distance(snapped_segment[0], snapped_segment[1]) > tolerance_m:
            snapped.append((snapped_segment[0], snapped_segment[1]))
    return snapped, len(representatives)


def _signed_area(polygon: Sequence[Point]) -> float:
    return 0.5 * sum(
        polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
        - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
        for index in range(len(polygon))
    )


def trace_room_polygons(
    segments: Iterable[Segment],
    *,
    snap_tolerance_m: float = 0.05,
    minimum_area_m2: float = 0.25,
) -> list[list[Point]]:
    """Trace bounded planar faces from metric wall segments.

    Segments are snapped into a graph, then each directed edge follows the
    next clockwise edge at the destination. The unbounded exterior face is
    removed by area, leaving room candidates in metric coordinates.
    """
    normalized, _ = _snap_points(list(segments), snap_tolerance_m)
    outgoing: dict[Point, list[Point]] = {}
    for start, end in normalized:
        outgoing.setdefault(start, []).append(end)
        outgoing.setdefault(end, []).append(start)
    for node, neighbors in outgoing.items():
        neighbors.sort(key=lambda point: atan2(point[1] - node[1], point[0] - node[0]))

    visited: set[tuple[Point, Point]] = set()
    faces: list[list[Point]] = []
    for start, neighbors in outgoing.items():
        for end in neighbors:
            if (start, end) in visited:
                continue
            face: list[Point] = []
            current = (start, end)
            while current not in visited:
                visited.add(current)
                origin, destination = current
                face.append(origin)
                candidates = outgoing[destination]
                reverse_index = candidates.index(origin)
                next_neighbor = candidates[(reverse_index - 1) % len(candidates)]
                current = (destination, next_neighbor)
            if current[0] == start and len(face) >= 3:
                area = _signed_area(face)
                if abs(area) >= minimum_area_m2:
                    faces.append(face)

    if not faces:
        return []
    # The clockwise walk yields the unbounded face with the opposite winding.
    # Keeping the positive winding also works when a single room has no
    # larger outer boundary to compare against.
    return [face for face in faces if _signed_area(face) >= minimum_area_m2]


def polygon_area_m2(polygon: Sequence[Point]) -> float:
    return abs(_signed_area(polygon))
