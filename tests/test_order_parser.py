# -*- coding: utf-8 -*-

import unittest

from backend.order_parser import parse_order_text


class OrderParserTests(unittest.TestCase):
    def test_complete_chinese_order_is_extracted(self) -> None:
        result = parse_order_text("客户：海川制造；产品：伺服电机；数量：20台；交期：2026年9月10日")
        self.assertEqual(result["order"]["customer_name"], "海川制造")
        self.assertEqual(result["order"]["product_name"], "伺服电机")
        self.assertEqual(result["order"]["quantity"], 20.0)
        self.assertEqual(result["order"]["promised_date"], "2026-09-10")
        self.assertTrue(result["ready_for_review"])
        self.assertTrue(result["requires_human_confirmation"])

    def test_missing_fields_are_not_invented(self) -> None:
        result = parse_order_text("客户：海川制造，要20台")
        self.assertIsNone(result["order"]["product_name"])
        self.assertIn("product_name", result["missing_fields"])
        self.assertFalse(result["ready_for_review"])

    def test_empty_text_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            parse_order_text("  ")

    def test_invalid_date_is_reported_missing(self) -> None:
        result = parse_order_text("客户：海川；产品：电机；数量：2台；交期：2026-13-40")
        self.assertIsNone(result["order"]["promised_date"])
        self.assertIn("promised_date", result["missing_fields"])


if __name__ == "__main__":
    unittest.main()
