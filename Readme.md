# Pranalika

Pranalika is a starter engineering scaffold for a handheld property-scanning system that converts phone captures into a dimensioned whole-property floor plan with shared geometry, damage, and confidence outputs across photo, video, and LiDAR capture tiers.

## Quick start

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m property_scan --tier photo --input /path/to/property --output /tmp/property_plan.json
PYTHONPATH=src python -m property_scan --tier photo --input /path/to/property --output /tmp/property_plan.json --ground-truth /path/to/ground_truth.json --benchmark-output /tmp/benchmark.json
```

## What is included

- a common output contract shared by all tiers
- a photo pipeline skeleton for per-room folders
- a video pipeline skeleton for walkthrough inputs
- a LiDAR pipeline skeleton for depth/pose-driven data
- a benchmark and capture protocol designed around the assignment
- a technical report overlaying the architecture and drift strategy
- a selected-stack strategy grounded in the sample repos: Room-Reconstruction-Demo, RoomPlanDemo, openPlan3D, and COLMAP

## Selected open-source stack

The sample repositories provided in the data folder point to a very specific and practical architecture for this assignment:

- Room-Reconstruction-Demo: photo-tier reconstruction baseline using depth estimation and room reconstruction
- RoomPlanDemo: LiDAR-tier capture and room geometry reference using Apple RoomPlan
- openPlan3D: final whole-property editing and room adjacency layer
- COLMAP: camera pose and sparse reconstruction backbone for photo/video geometry

This repo is intentionally built around that stack rather than a blind "AI model only" approach.

## Repository structure

- `src/property_scan/` — package code
- `docs/` — compliance matrix, capture protocol, device matrix, technical report
- `benchmark/` — benchmark logic and scoring notes
- `tests/` — smoke validation for the output contract and CLI

## Notes

This project is intentionally a practical baseline rather than a full production scanner. The repository establishes the architecture, shared output format, and team execution plan needed for the assignment while remaining honest about the absence of raw benchmark captures in this workspace.

## Independent ground truth

The real captures under `data/` contain sensor inputs, not independently measured labels. Use the
schema in `docs/ground_truth_manifest.example.json` to provide measured room dimensions and opening
widths. The CLI compares the generated plan to that manifest using the assignment tolerances and
writes a separate benchmark report. It fails on room, wall, or opening identity mismatches rather
than silently scoring an incomplete comparison.

## Geometry quality gates

The real-capture path now reports qualified vertical wall planes and their
metric horizontal spans. Photo output uses those spans as wall measurements
only when at least four planes pass the vertical-span and residual checks;
otherwise it emits the room-area/aspect estimate with explicit fallback
provenance. This prevents visually plausible but unqualified geometry from
being presented as assignment-validated measurements.

`property_scan.room_polygon.trace_room_polygons` independently converts
snapped metric wall segments into bounded room faces using planar graph
tracing and shoelace area. It is designed to become the topology layer for
shared walls and wall-hosted openings; it does not copy implementation code
from the reference repositories.

Qualified wall planes also expose robust horizontal and vertical extents.
These extents are the metric evidence needed for the next opening stage;
they are not yet treated as door/window ground truth without independent
opening validation.

The opening stage now reports internal gaps in wall-plane support as
`wall-opening candidates`. These candidates include a metric interval,
estimated width, and evidence confidence, but are deliberately not promoted
to door/window measurements because occlusion and incomplete scan coverage
can create identical gaps.

Each candidate is retained in the photo room's `scope_items` with its source
plane and horizontal interval, rather than exposing only an aggregate count.
The default candidate gate accepts widths from 0.45 m through 2.5 m; broader
holes are treated as incomplete wall coverage rather than openings.

Whole-property stitching now validates room-link drift before declaring the
layout connected. Links above the 0.25 m default drift threshold are rejected,
and the validator reports connected components and rejected edges instead of
silently averaging disconnected rooms into one property layout.

Photo plans now include this stitching result in `stitching_notes` and
`layout_drift_m`; the hallway chain remains an inferred connection until
overlap or doorway evidence is available.
