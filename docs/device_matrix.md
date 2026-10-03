# Device matrix

| Tier | Hardware | Typical rooms supported | Accuracy expectation | Confidence posture |
|---|---|---:|---|---|
| Photo | iPhone 15 or newer | 2-8 photos per room, multi-room property | ±8% wall-length accuracy | Wider confidence bounds because geometry is inferred from stills |
| Video | iPhone 15 or newer | Handheld walkthrough | ±3% wall-length accuracy | Moderate, subject to drift and loop closure quality |
| LiDAR | Pro-class iPhone with depth and pose | Highest fidelity rooms | Best metric fidelity; lowest uncertainty | Tightest confidence intervals |

## Capture guidance

- Photos are the easiest and broadest path for field capture, but they require careful overlap and room-level consistency.
- Video captures improve continuity but demand disciplined phone motion and explicit drift correction.
- LiDAR provides the strongest baseline, especially for ceiling height, openings, and structural geometry.

## Recommendation

For a short execution window, the best practical strategy is to support all three tiers behind the same JSON output contract, with confidence intervals widened by tier quality and scene difficulty. This preserves the assignment’s key requirement: the downstream consumer sees the same plan representation regardless of sensor source.
