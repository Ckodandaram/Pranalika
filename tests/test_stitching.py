import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from property_scan.stitching import estimate_layout_drift, stitch_room_graph


class TestStitching(unittest.TestCase):
    def test_stitch_room_graph_builds_hallway_connections(self):
        graph = stitch_room_graph(["room_1", "room_2", "room_3"])
        self.assertEqual(len(graph), 2)
        self.assertEqual(graph[0].from_room, "room_1")
        self.assertEqual(graph[0].to_room, "room_2")

    def test_estimate_layout_drift_handles_multi_room_output(self):
        graph = [
            __import__("property_scan.stitching", fromlist=["RoomConnection"]).RoomConnection("room_1", "room_2", "hallway", 0.015),
            __import__("property_scan.stitching", fromlist=["RoomConnection"]).RoomConnection("room_2", "room_3", "hallway", 0.012),
        ]
        drift = estimate_layout_drift(["room_1", "room_2", "room_3"], graph)
        self.assertAlmostEqual(drift, 0.0135, places=4)


if __name__ == "__main__":
    unittest.main()
