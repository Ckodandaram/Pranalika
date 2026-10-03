from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class RoomConnection:
    from_room: str
    to_room: str
    connection_type: str
    drift_m: float = 0.0


def stitch_room_graph(rooms: Iterable[str], connections: Iterable[tuple[str, str, str]] | None = None) -> list[RoomConnection]:
    room_ids = list(rooms)
    if not room_ids:
        return []

    edges = []
    for source, target, connection_type in (connections or []):
        if source in room_ids and target in room_ids:
            edges.append(RoomConnection(from_room=source, to_room=target, connection_type=connection_type, drift_m=0.0))

    if not edges and len(room_ids) > 1:
        for index in range(len(room_ids) - 1):
            edges.append(RoomConnection(from_room=room_ids[index], to_room=room_ids[index + 1], connection_type="hallway", drift_m=0.0))

    return edges


def estimate_layout_drift(rooms: Iterable[str], room_graph: Iterable[RoomConnection]) -> float:
    room_list = list(rooms)
    if len(room_list) <= 1:
        return 0.0
    graph = list(room_graph)
    if not graph:
        return 0.0
    return round(sum(edge.drift_m for edge in graph) / max(1, len(graph)), 4)
