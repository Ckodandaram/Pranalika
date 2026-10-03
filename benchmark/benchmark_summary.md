# Benchmark summary

## Required benchmark set

- 3-room multi-room capture plus hallway: required
- furnished damaged room with two damage classes: required
- identical rooms captured in photo, video, and LiDAR: required
- same room repeated at least twice at the same tier: required
- ground truth via laser or tape measurements: required

## Expected evaluation gates

| Metric | Gate |
|---|---:|
| Opening width | ≤ 2 cm error on 85% of openings |
| Ceiling height | ≤ 1.5 cm per room |
| Repeatability | ≤ 1 cm or 0.5% per wall |
| Photo wall lengths | ±8% |
| Video wall lengths | ±3% |
| Multi-room drift | corrected via loop closure / pose-graph / plane anchoring |

## Proposed benchmarking workflow

1. Record the same 3-room suite in all three tiers.
2. Repeat one room twice at the same tier to measure repeatability.
3. Capture one damaged room with at least two damage classes.
4. Measure each room with a laser measurer or tape and preserve raw sensor logs.
5. Run all three processing paths through the same JSON output contract.
6. Compare between real measurements and generated plan metrics.
7. Run the consumer-app baseline on two rooms and compare dimension by dimension.

## Fix loop entry point

The single worst-performing gate should be selected from the benchmark result. The fix loop then follows this sequence:

- diagnose root cause with evidence
- predict the expected improvement
- implement the fix in the geometry or drift path
- rerun the same benchmark
- compare before vs after in a reproducible output bundle
