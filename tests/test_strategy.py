import unittest

from property_scan.strategy import pipeline_selection, selected_stack


class TestStrategySelection(unittest.TestCase):
    def test_selected_stack_has_all_required_components(self):
        stack = selected_stack()
        names = {item.name for item in stack}
        self.assertIn("Room-Reconstruction-Demo", names)
        self.assertIn("RoomPlanDemo", names)
        self.assertIn("openPlan3D", names)
        self.assertIn("COLMAP", names)

    def test_pipeline_selection_covers_all_tiers(self):
        tiers = pipeline_selection()
        self.assertIn("photo", tiers)
        self.assertIn("video", tiers)
        self.assertIn("lidar", tiers)
        self.assertIn("whole_property", tiers)


if __name__ == "__main__":
    unittest.main()
