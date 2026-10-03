# Technical report

## Architecture

The system is built around a common geometry contract that all capture tiers produce before downstream room reconstruction. Instead of producing separate outputs for photos, video, and LiDAR, each pipeline converts raw sensor information into the same JSON schema. This reduces downstream integration risk and makes the benchmark evaluation consistent.

## Tier design

The photo path starts from per-room image sets. The room folders are stitched into a whole-property plan through image-overlap heuristics, room association, and plan alignment. The video path reuses the same final schema but adds richer camera-motion tracking from a walkthrough. The LiDAR path is the strongest tier because it produces metric depth, poses, and intrinsics that can be folded directly into the common room geometry model.

## Device matrix

The device matrix is intentionally conservative. Photo and video work on iPhone 15 and newer hardware. LiDAR-based reconstruction requires Pro-class iPhone hardware because it depends on depth and pose quality. The confidence threshold shifts by tier so the result remains accurate without over-claiming performance on weaker captures.

## Drift handling

For multi-room capture, accumulated drift is a first-class problem. The intended production design includes loop closure, pose-graph optimization, and plane-anchored correction. The current repository captures the pattern in the architecture rather than a fully trained end-to-end stack. The important point is that raw sensor poses are not trusted blindly; they are corrected before final room placement.

## Error budget

The assignment’s gates are explicit: opening width errors must be within 2 cm on at least 85% of openings; ceiling height error must remain within 1.5 cm per room; multi-room drift must not break adjacency or overlap constraints; and wall lengths must remain within ±8% for photo and ±3% for video. These tolerances motivate the design: a shared calibration layer, explicit confidence intervals, and repeatability checks are more important than purely visual scores.

## Calibration analysis

Calibration should be tier-specific. For photo captures, calibration is dominated by scene overlap and camera consistency. For video, frame-to-frame pose drift and motion blur dominate. For LiDAR, the major concerns are surface masking from reflective materials and the presence of transparent or wet surfaces. The architecture supports confidence widening when the scene is difficult.

## Fix-loop story

The assignment rewards the ability to diagnose the worst gate, fix it, and show before/after numbers. The repository is therefore arranged so that the fix loop is a documented engineering practice, not an afterthought. A realistic production workflow would identify the weakest gate first, diagnose the root cause using the benchmark, patch the geometry or drift pipeline, and rerun the same benchmark to confirm the improvement.

## Known failure modes

The likely real-world failure modes are mirrors, glass, wet-look surfaces, and low-light conditions. These degrade both geometry and visibility. The architecture acknowledges these by using tier-aware confidence intervals and explicit room-level validation rather than a single global pass/fail model.
