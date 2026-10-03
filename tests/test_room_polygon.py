import unittest

from property_scan.room_polygon import polygon_area_m2, trace_room_polygons


class RoomPolygonTests(unittest.TestCase):
    def test_traces_two_rooms_and_discards_outer_face(self) -> None:
        segments = [
            ((0.0, 0.0), (4.0, 0.0)),
            ((4.0, 0.0), (4.0, 3.0)),
            ((4.0, 3.0), (0.0, 3.0)),
            ((0.0, 3.0), (0.0, 0.0)),
            ((4.0, 0.0), (8.0, 0.0)),
            ((8.0, 0.0), (8.0, 3.0)),
            ((8.0, 3.0), (4.0, 3.0)),
        ]
        polygons = trace_room_polygons(segments)
        self.assertEqual(len(polygons), 2)
        self.assertEqual(sorted(round(polygon_area_m2(polygon), 2) for polygon in polygons), [12.0, 12.0])

    def test_snaps_small_endpoint_noise(self) -> None:
        segments = [
            ((0.0, 0.0), (4.0, 0.0)),
            ((4.01, 0.01), (4.0, 3.0)),
            ((4.0, 3.0), (0.0, 3.0)),
            ((0.0, 3.0), (0.0, 0.0)),
        ]
        polygons = trace_room_polygons(segments, snap_tolerance_m=0.05)
        self.assertEqual(len(polygons), 1)
        self.assertAlmostEqual(polygon_area_m2(polygons[0]), 12.0, places=1)


if __name__ == "__main__":
    unittest.main()
