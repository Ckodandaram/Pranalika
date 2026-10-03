# Capture protocol

## Recommended route

Use a stock capture protocol with a normal iPhone. The protocol is intentionally simple enough that a homeowner or assessor can follow it without training.

## One-page walkthrough

1. Install a standard LiDAR logging or room capture app if the target device supports it.
2. Walk each room in a clockwise pattern.
3. Aim for 2-8 photos per room for photo mode, or a 30-90 second walkthrough in video mode.
4. Keep the camera roughly 1.1-1.5 m high and avoid heavy motion blur.
5. Do not capture through mirrors, glass walls, or wet-looking surfaces.
6. Ensure overlap between adjacent images or video frames.
7. For multi-room properties, include one connector or hallway between room groups.
8. Transfer files into a single `property/` directory with room folders named consistently.

## What to avoid

- backtracking without overlap
- moving too fast during video capture
- shooting through reflective surfaces
- strong backlighting or very dark rooms
- incomplete room coverage

## Transfer format

```text
property/
  room_1/
    img001.jpg
    img002.jpg
  room_2/
    img001.jpg
    img002.jpg
  hallway/
    img001.jpg
```

## Reproducibility rules

- keep the same room names across capture runs
- record the same measurement targets with every benchmark run
- preserve raw sensor files for replay and evaluation
- use the same processing command for all benchmark outputs
