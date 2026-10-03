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

Video and LiDAR plans expose the same connectivity and stitching quality
status. This keeps the output contract consistent across capture tiers while
retaining tier-specific drift estimates.

Benchmark output also includes `reconstruction_quality`. Accuracy summaries
are accompanied by confidence-coverage and trajectory-consistency gates, and
`validated_for_accuracy_claims` is false whenever any capture fails either
gate. This keeps proxy benchmark numbers separate from trustworthy assignment
claims.

Opening benchmark output is split into `opening_width` and
`opening_evidence`. The former is a proxy comparison until an independent
ground-truth manifest is supplied; the latter contains the detected wall-gap
candidate widths and source intervals for review.

The CLI writes this assignment benchmark directly when `--benchmark-output` is
provided for a photo data root without `--ground-truth`. When
`--ground-truth` is provided, the same option continues to write the
independent measurement comparison report instead.

Photo rooms also expose a `room_boundary_candidate` scope item containing the
floor-aligned registered-depth polygon, metric area, horizontal basis vectors,
and a `validated` flag. The polygon is retained as reconstruction evidence
until wall topology and independent measurements confirm it.

Each room also reports `boundary_wall_evidence_comparison`, including the
footprint area, the area implied by qualified wall spans, their disagreement
ratio, and a conservative consistency flag. This is a cross-check, not an
accuracy claim.

`room_geometry_quality_gate` combines confidence coverage, a minimum of four
qualified wall planes, and no more than 25% footprint/wall-area disagreement.
Only rooms passing all three checks are eligible for future metric promotion;
the current sample captures remain diagnostic.

The benchmark artifact also includes `geometry_evidence`, combining the same
room-level gate with footprint area, wall-derived area, and disagreement ratio.
The aggregate `validated_for_measurement_claims` flag remains false unless
every evaluated capture passes.

Every generated `PropertyPlan` now carries `quality_gates` and
`measurement_claims_validated`. The latter remains false until stitching,
room geometry, and independent ground-truth requirements are all satisfied;
diagnostic estimates remain available without being presented as validated
assignment measurements.

Before serialization, every pipeline now validates room IDs, opening IDs,
positive finite measurements, and non-negative layout drift. Stitching
connections also preserve their drift and verified status in the JSON output,
so rejected links are visible to downstream consumers.

The contract also verifies that an opening's physical width fits within its
host wall at the normalized position, and that whole-property connections
reference rooms present in the same plan.

CLI plan JSON also includes `validation_summary` with room count, connection
count, verified-connection count, and measurement-claim status.

Plan JSON also includes `assignment_readiness`, a single decision surface
covering stitching, room geometry, independent ground truth, and the fraction
of openings that have actually been validated. Prototype opening estimates
remain visible but are reported as blockers rather than being promoted into
assignment claims.

The CLI also writes a reviewer-facing `<plan>.status.json` artifact by default
(or to `--status-output`). It summarizes implemented requirements, blocked
requirements, prioritized next actions, and whether an accuracy claim is
allowed. Its `diagnostic_only` status is intentional when independent physical
ground truth is unavailable.

Before an independent benchmark runs, the CLI performs a ground-truth coverage
check for room IDs, wall counts, ceiling heights, and opening identities. An
incomplete manifest is rejected with a structured coverage report instead of
producing a misleading partial accuracy result.

Assignment benchmark artifacts include a versioned `report_provenance` section
and an `assignment_readiness` decision. Readiness is intentionally false until
an independent ground-truth manifest is supplied and the confidence,
trajectory, and room-geometry gates pass. The blockers and next action are
serialized explicitly so a proxy benchmark cannot be mistaken for an accuracy
claim.

Proxy benchmark artifacts use schema version `1.2.0` and retain every
per-measurement result, not only aggregate counts. The artifact validator
rejects missing metric details or provenance that incorrectly claims independent
ground truth before the JSON is written.

Readiness reports also include prioritized blocker details with severity and a
concrete remediation action. Proxy reports include capture-level counts for
confidence, trajectory, and room-geometry gates so reviewers can identify
whether a failure is isolated or systemic.

When an independent ground-truth manifest is supplied, the CLI now validates
the generated plan before comparison and updates the persisted plan with the
ground-truth gate result. `measurement_claims_validated` becomes true only
when the independent comparison, stitching, and room-geometry gates all pass.
Proxy benchmark reports include explicit provenance showing that they are not
independent ground truth.

Independent benchmark reports are versioned and include the assignment
tolerances plus an `assignment_readiness` section. A passing measurement
comparison alone does not set the plan's validated claim flag: stitching and
room-geometry gates must also pass. The report lists each remaining blocker
and the next action explicitly.

Independent reports also retain per-room results for ceiling height, wall
length, and opening width. The report validator requires those room-level
results, aggregate metric coverage, and an explicit independent-validation
marker before the CLI writes the artifact.

They also include `room_summary` and `quality_gates`, making the distinction
between measurement tolerance success and stitching/geometry readiness visible
without inspecting the generated plan separately.

Every emitted opening now includes `source` and `validated` fields. Current
photo, video, and LiDAR baseline openings are explicitly marked as estimates;
wall-support gap candidates remain separate evidence until an opening detector
and independent measurements validate them.

Openings also carry a `wall_index` and normalized `position_ratio`. Contract
validation rejects references to missing walls or positions outside `[0, 1]`,
so downstream editors can host each opening on a specific wall segment.
