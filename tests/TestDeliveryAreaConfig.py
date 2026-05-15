# -*- coding: utf-8 -*-
import unittest

from src.data import delivery_area


class TestDeliveryAreaConfig(unittest.TestCase):
    def test_get_transfer_search_area_returns_preset_config(self):
        self.assertEqual(
            delivery_area.get_transfer_search_area("武陵城", "武陵"),
            {"preset": "top"},
        )
        self.assertEqual(
            delivery_area.get_transfer_search_area("试验园区", "武陵"),
            {"preset": "right"},
        )

    def test_get_transfer_search_area_supports_custom_box_config(self):
        area_name = "测试区域"
        delivery_area.DELIVERY_AREA_CONFIG[area_name] = {
            "delivery_locations": ["测试点"],
            "delivery_targets_by_location": {"测试点": []},
            "transfer_search_area": {
                "测试点": {"x": 0.1, "y": 0.2, "to_x": 0.8, "to_y": 0.9},
            },
            "ocr_priority_locations": ["测试点"],
        }
        try:
            self.assertEqual(
                delivery_area.get_transfer_search_area("测试点", area_name),
                {"x": 0.1, "y": 0.2, "to_x": 0.8, "to_y": 0.9},
            )
        finally:
            delivery_area.DELIVERY_AREA_CONFIG.pop(area_name, None)


if __name__ == "__main__":
    unittest.main()
