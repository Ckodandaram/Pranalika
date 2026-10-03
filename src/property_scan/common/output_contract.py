from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional


@dataclass
class ConfidenceInterval:
    low: float
    high: float
    unit: str = "m"
    coverage: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "low": self.low,
            "high": self.high,
            "unit": self.unit,
            "coverage": self.coverage,
        }


@dataclass
class Measurement:
    value: float
    unit: str = "m"
    confidence: Optional[ConfidenceInterval] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"value": self.value, "unit": self.unit}
        if self.confidence is not None:
            payload["confidence"] = self.confidence.to_dict()
        return payload


@dataclass
class DamageRecord:
    id: str
    damage_class: str
    metric_extent: Measurement
    region: str
    concealed_damage: bool = False
    concealed_damage_rule: str = "N/A"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "damage_class": self.damage_class,
            "metric_extent": self.metric_extent.to_dict(),
            "region": self.region,
            "concealed_damage": self.concealed_damage,
            "concealed_damage_rule": self.concealed_damage_rule,
        }


@dataclass
class Opening:
    id: str
    type: str
    width: Measurement
    height: Measurement
    location: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "width": self.width.to_dict(),
            "height": self.height.to_dict(),
            "location": self.location,
        }


@dataclass
class Room:
    id: str
    name: str
    floor_area: Measurement
    ceiling_height: Measurement
    walls: List[Measurement] = field(default_factory=list)
    openings: List[Opening] = field(default_factory=list)
    damage: List[DamageRecord] = field(default_factory=list)
    scope_items: List[Dict[str, Any]] = field(default_factory=list)
    adjacency: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "floor_area": self.floor_area.to_dict(),
            "ceiling_height": self.ceiling_height.to_dict(),
            "walls": [wall.to_dict() if hasattr(wall, "to_dict") else wall for wall in self.walls],
            "openings": [opening.to_dict() for opening in self.openings],
            "damage": [record.to_dict() for record in self.damage],
            "scope_items": self.scope_items,
            "adjacency": self.adjacency,
        }


@dataclass
class PropertyPlan:
    capture_tier: str
    property_id: str
    rooms: List[Room]
    whole_property_connections: List[Dict[str, Any]] = field(default_factory=list)
    schema_version: str = "1.0.0"
    generated_by: str = "property_scan"
    layout_drift_m: float = 0.0
    stitching_notes: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)
    measurement_claims_validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capture_tier": self.capture_tier,
            "property_id": self.property_id,
            "schema_version": self.schema_version,
            "generated_by": self.generated_by,
            "layout_drift_m": self.layout_drift_m,
            "stitching_notes": self.stitching_notes,
            "quality_gates": self.quality_gates,
            "measurement_claims_validated": self.measurement_claims_validated,
            "rooms": [room.to_dict() for room in self.rooms],
            "whole_property_connections": self.whole_property_connections,
        }


def confidence_interval_for_tier(tier: str, nominal: float) -> ConfidenceInterval:
    tier_bandwidth = {
        "photo": 0.08,
        "video": 0.03,
        "lidar": 0.015,
    }.get(tier.lower(), 0.08)

    half_width = nominal * tier_bandwidth
    return ConfidenceInterval(low=nominal - half_width, high=nominal + half_width, unit="m")


def validate_plan_contract(plan: PropertyPlan) -> None:
    """Reject malformed plans before they are persisted or benchmarked."""
    if not plan.property_id.strip():
        raise ValueError("property_id must be non-empty")
    room_ids: set[str] = set()
    for room in plan.rooms:
        if not room.id.strip():
            raise ValueError("room id must be non-empty")
        if room.id in room_ids:
            raise ValueError(f"duplicate room id: {room.id}")
        room_ids.add(room.id)
        measurements = [room.floor_area, room.ceiling_height, *room.walls]
        for measurement in measurements:
            if not math.isfinite(measurement.value) or measurement.value <= 0:
                raise ValueError(f"{room.id} measurements must be finite and positive")
        opening_ids: set[str] = set()
        for opening in room.openings:
            if opening.id in opening_ids:
                raise ValueError(f"duplicate opening id in room {room.id}")
            opening_ids.add(opening.id)
            if not math.isfinite(opening.width.value) or opening.width.value <= 0:
                raise ValueError(f"{room.id} opening width must be finite and positive")
            if not math.isfinite(opening.height.value) or opening.height.value <= 0:
                raise ValueError(f"{room.id} opening height must be finite and positive")
    if not math.isfinite(plan.layout_drift_m) or plan.layout_drift_m < 0:
        raise ValueError("layout_drift_m must be finite and non-negative")
