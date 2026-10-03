# Pranalika

Pranalika is a starter engineering scaffold for a handheld property-scanning system that converts phone captures into a dimensioned whole-property floor plan with shared geometry, damage, and confidence outputs across photo, video, and LiDAR capture tiers.

## Quick start

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m property_scan --tier photo --input /path/to/property --output /tmp/property_plan.json
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

