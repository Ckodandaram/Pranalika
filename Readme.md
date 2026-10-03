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

## Repository structure

- `src/property_scan/` — package code
- `docs/` — compliance matrix, capture protocol, device matrix, technical report
- `benchmark/` — benchmark logic and scoring notes
- `tests/` — smoke validation for the output contract and CLI

## Notes

This project is intentionally a practical baseline rather than a full production scanner. The repository establishes the architecture, shared output format, and team execution plan needed for the assignment while remaining honest about the absence of raw benchmark captures in this workspace.

