# -*- coding: utf-8 -*-

import unittest

from backend.contract_engine import review_contract_text


class ContractEngineTests(unittest.TestCase):
    def test_extracts_key_terms_with_evidence(self) -> None:
        result = review_contract_text("合同编号：HT-01；甲方：智造厂；乙方：供应商；合同金额：100000元；付款方式：验收后30日付款；交货日期：2026年9月1日；违约责任：延期每日赔偿合同额0.1%；争议由甲方所在地法院管辖。")
        self.assertEqual(result["contract"]["contract_no"], "HT-01")
        self.assertEqual(result["contract"]["party_a"], "智造厂")
        self.assertTrue(any(item["field"] == "payment_terms" for item in result["evidence"]))

    def test_missing_terms_are_flagged_not_invented(self) -> None:
        result = review_contract_text("甲方：智造厂；乙方：供应商。")
        self.assertIsNone(result["contract"]["payment_terms"])
        self.assertIn("付款条款", result["missing_clauses"])
        self.assertEqual(result["overall_risk"], "high")

    def test_blank_field_is_high_risk(self) -> None:
        result = review_contract_text("合同金额：____；付款方式：验收后付款；交货日期：待定")
        self.assertTrue(any(item["category"] == "文本完整性" and item["level"] == "high" for item in result["findings"]))

    def test_full_prepayment_depends_on_user_position(self) -> None:
        buyer = review_contract_text("付款方式：100%预付；交货日期：2026年9月1日；违约责任：延期赔偿；争议由法院管辖。", "采购方")
        self.assertTrue(any(item["category"] == "付款条款" and item["level"] == "high" for item in buyer["findings"]))

    def test_empty_contract_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            review_contract_text("  ")


if __name__ == "__main__":
    unittest.main()
