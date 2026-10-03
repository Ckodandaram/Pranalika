from __future__ import annotations

import argparse
import json
from pathlib import Path

from property_scan.pipeline import build_lidar_plan, build_photo_plan, build_video_plan


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a common property floor-plan output from a capture tier.")
    parser.add_argument("--tier", choices=["photo", "video", "lidar"], required=True, help="Capture tier to process")
    parser.add_argument("--input", required=True, help="Input directory or file; for photo it is a room folder root, for video a .mp4, for lidar a capture directory")
    parser.add_argument("--output", required=True, help="JSON output path")
    parser.add_argument("--property-id", default="demo_property", help="Identifier for the output property")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.tier == "photo":
        plan = build_photo_plan(args.input, args.property_id)
    elif args.tier == "video":
        plan = build_video_plan(args.input, args.property_id)
    else:
        plan = build_lidar_plan(args.input, args.property_id)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    print(f"Wrote plan to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
