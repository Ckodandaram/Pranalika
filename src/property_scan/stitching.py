from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class RoomConnection:
    from_room: str
    to_room: str
    connection_type: str
    drift_m: float = 0.0
    verified: bool = True


def stitch_room_graph(
    rooms: Iterable[str],
    connections: Iterable[tuple[str, str, str]] | None = None,
    *,
    edge_drifts_m: dict[tuple[str, str], float] | None = None,
    max_edge_drift_m: float = 0.25,
) -> list[RoomConnection]:
    room_ids = list(rooms)
    if not room_ids:
        return []

    edges = []
    for source, target, connection_type in (connections or []):
        if source in room_ids and target in room_ids:
            drift = float((edge_drifts_m or {}).get((source, target), 0.0))
            edges.append(RoomConnection(
                from_room=source,
                to_room=target,
                connection_type=connection_type,
                drift_m=round(drift, 4),
                verified=drift <= max_edge_drift_m,
            ))

    if not edges and len(room_ids) > 1:
        for index in range(len(room_ids) - 1):
            edges.append(RoomConnection(
                from_room=room_ids[index],
                to_room=room_ids[index + 1],
                connection_type="hallway",
                drift_m=0.0,
            ))

    return edges


def estimate_layout_drift(rooms: Iterable[str], room_graph: Iterable[RoomConnection]) -> float:
    room_list = list(rooms)
    if len(room_list) <= 1:
        return 0.0
    graph = list(room_graph)
    if not graph:
        return 0.0
    verified_edges = [edge for edge in graph if edge.verified]
    if not verified_edges:
        return 0.0
    return round(sum(edge.drift_m for edge in verified_edges) / len(verified_edges), 4)


def connected_room_components(
    rooms: Iterable[str],
    room_graph: Iterable[RoomConnection],
) -> list[list[str]]:
    """Return connected components using only verified room links."""
    room_ids = list(dict.fromkeys(rooms))
    adjacency = {room_id: set() for room_id in room_ids}
    for edge in room_graph:
        if edge.verified and edge.from_room in adjacency and edge.to_room in adjacency:
            adjacency[edge.from_room].add(edge.to_room)
            adjacency[edge.to_room].add(edge.from_room)

    components: list[list[str]] = []
    remaining = set(room_ids)
    while remaining:
        root = next(iter(remaining))
        stack = [root]
        component: list[str] = []
        remaining.remove(root)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda component: component[0])


def validate_room_graph(
    rooms: Iterable[str],
    room_graph: Iterable[RoomConnection],
    *,
    max_layout_drift_m: float = 0.25,
) -> dict[str, object]:
    """Report whether verified links connect the complete property."""
    room_ids = list(dict.fromkeys(rooms))
    graph = list(room_graph)
    components = connected_room_components(room_ids, graph)
    drift = estimate_layout_drift(room_ids, graph)
    return {
        "passed": len(components) <= 1 and drift <= max_layout_drift_m,
        "connected": len(components) <= 1,
        "component_count": len(components),
        "components": components,
        "layout_drift_m": drift,
        "max_layout_drift_m": max_layout_drift_m,
        "rejected_edges": [
            {"from": edge.from_room, "to": edge.to_room, "drift_m": edge.drift_m}
            for edge in graph
            if not edge.verified
        ],
    }
