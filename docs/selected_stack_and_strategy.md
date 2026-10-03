# Selected stack and assignment strategy

## What each repo contributes

### 1) Room-Reconstruction-Demo-main
Role: photo-tier baseline

This is the closest match to the assignment's photo requirement. It uses a practical room-photo pipeline: multiple images, depth estimation, point-cloud fusion, and floor-plan generation. The main value is that it directly addresses the hardest input tier from the case study: no sensor poses, no depth, and only 2–8 photos per room.

Why this matters for the assignment:

- it aligns with the photo requirement from the case study
- it demonstrates a room-level reconstruction flow that can be adapted to multi-room stitching
- it supplies the right technical direction: camera geometry + depth inference + 2D plan extraction

### 2) RoomPlanDemo-main
Role: LiDAR-tier reference implementation

This is the strongest example of the Apple RoomPlan path. It shows how a LiDAR scan becomes a room geometry model and then a 2D floor plan with editability and export. It is not enough on its own for the whole assignment, but it gives us the correct geometric contract for the LiDAR tier.

Why this matters for the assignment:

- it matches the LiDAR capture requirement
- it demonstrates room boundaries, wall geometry, openings, and interactive editing in a real app
- it gives a clean reference for a high-confidence geometric baseline

### 3) openPlan3D-main
Role: whole-property editor and output contract

This is the best fit for the final product layer of the assignment: a whole-property floor-plan editor with room adjacency, wall editing, and 3D preview. It matches the assignment's requirement that all tiers eventually converge to the same output contract.

Why this matters for the assignment:

- it is already structured around room geometry and floor-plan editing
- it handles multi-room layout and connection logic more naturally than a single-room scan pipeline
- it is the right downstream representation for the final stitched property plan

### 4) colmap-main
Role: geometric backbone for photo/video processing

COLMAP provides the camera pose estimation and sparse reconstruction backbone required when there are no raw poses. This is especially important for the video tier and for stitching room-level reconstructions into a multi-room property.

Why this matters for the assignment:

- feature extraction and matching are essential for weakly calibrated inputs
- camera-pose estimation gives us drift-aware room registration
- same-room repeatability and multi-room drift correction are both easier if the camera motion is estimated explicitly

## Final approach

We will not build four unrelated systems. Instead, we will build a single common pipeline with three inputs and one shared output contract.

Photo path
- input: per-room photo folders
- use Room-Reconstruction-Demo logic as the baseline
- add COLMAP or structure-from-motion for pose estimation where available
- estimate per-room geometry and scale
- generate room polygons and openings

Video path
- input: handheld walkthrough video
- use frame-by-frame feature tracking and pose estimation
- reconstruct a consistent room graph with drift correction via loop closure or pose-graph optimization
- convert to the same room/adjacency contract as photo input

LiDAR path
- input: LiDAR depth + poses + intrinsics
- use RoomPlanDemo/RoomPlan geometry and room model as the high-confidence source
- treat it as the minimum metric baseline for the same output schema

Whole-property layer
- use openPlan3D-like room graph logic to connect rooms, hallways, doors, and layout adjacency
- minimize overlap while forcing a physically coherent room map

## Assignment-critical edge cases to address

### 1) Photo tier without depth or poses
This is the hardest case. The system must infer scale and structure from still images alone. The mitigation strategy is:

- use feature matching and SfM to recover relative geometry
- enforce a reference object / room scale calibration step
- allow wider confidence intervals and flag low-confidence rooms

### 2) Drift in multi-room stitching
The assignment explicitly warns that raw poses are not enough. We will handle this by:

- loop closure when revisiting the same hallway or room
- pose-graph optimization across adjacent rooms
- plane anchoring on shared walls and ceilings to stabilize the global map
- explicit before/after drift comparison

### 3) Weak surfaces and reflective materials
Mirrors, glass, and wet-look surfaces are major sources of false geometry. We will:

- mask likely reflective regions early
- down-weight them during surface reconstruction
- add conservative confidence intervals when the geometry is uncertain

### 4) Opening detection accuracy
Openings are easy to miss or hallucinate. We will enforce:

- geometric validation on door/window width and wall alignment
- a minimum opening presence check: if an opening is not supported by wall geometry, reject it
- a false-positive rejection rule for phantom openings on non-wall regions

### 5) Repeatability and calibration
Same room, same tier, same capture should reproduce practically the same plan. We will:

- keep the algorithm deterministic where possible
- fix random seeds in benchmarking runs
- compare same-room repeated scans against wall-length and ceiling-height tolerances

## Accuracy strategy

The assignment is not tolerant of vague "looks good" output. We will measure and calibrate by tier:

- photo tier: wall lengths target ±8%, wider confidence intervals
- video tier: wall lengths target ±3%, but with stronger drift controls
- LiDAR tier: strongest metric fidelity, with the tightest confidence intervals

For each room we will report:

- wall length
- opening width
- ceiling height
- floor area
- confidence interval
- repeatability measure

The key idea is that the output contract stays the same while the uncertainty grows honestly for weaker input sensors.

## Development milestones

1. Build a common schema and room graph model around the final output contract.
2. Wire in the photo-tier reconstruction using the Room-Reconstruction-Demo pattern.
3. Add the LiDAR-tier RoomPlan path using the RoomPlanDemo reference.
4. Add the video path using COLMAP/SLAM pose estimation plus drift correction.
5. Implement whole-property stitching using openPlan3D as the editor model.
6. Add benchmark tooling and a fix-loop dashboard.
7. Validate drift correction, opening detection, and repeatability against the assignment gates.

This is the practical path that matches the assignment requirement while staying grounded in the sample data and the open-source repositories already provided in the project.
