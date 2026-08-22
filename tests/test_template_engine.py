# -*- coding: utf-8 -*-

import unittest

from backend.template_engine import match_order_template


class TemplateEngineTests(unittest.TestCase):
    def test_fob_order_returns_export_path(self) -> None:
        result = match_order_template("FOB上海港出口订单，需要报关和海运")
        self.assertEqual(result["template"]["id"], "fob-export")
        self.assertEqual(result["confidence"], "high")
        self.assertIn("报关", result["template"]["matched_keywords"])

    def test_oem_order_returns_processing_path(self) -> None:
        result = match_order_template("这是OEM贴牌代工订单，图纸稍后发送")
        self.assertEqual(result["template"]["id"], "oem-processing")
        self.assertIn("图纸/规格", result["template"]["required_fields"])

    def test_promotion_order_returns_campaign_path(self) -> None:
        result = match_order_template("双11促销活动礼盒订单")
        self.assertEqual(result["template"]["id"], "promotion")

    def test_regular_order_falls_back_to_standard_with_reason(self) -> None:
        result = match_order_template("采购20台伺服电机")
        self.assertEqual(result["template"]["id"], "standard")
        self.assertIn("未识别", result["reason"])
        self.assertTrue(result["requires_human_confirmation"])


if __name__ == "__main__":
    unittest.main()
