# -*- coding: utf-8 -*-

import unittest

from backend.comparison_engine import compare_order_contract


class ComparisonEngineTests(unittest.TestCase):
    def test_accepted_orders_sync_to_data_core(self) -> None:
        """跨应用数据契约：接受的订单必须同步统一数据中心 orders 实体（PRD 9/19.11）。"""
        self.assertIn("syncToDataCore", self.source)
        self.assertIn("/zhiyun-data-core/imports/orders/commit?data_mode=production", self.source)
        self.assertIn('localStorage.getItem("zhiyun_token")', self.source)

    def test_consistent_fields(self) -> None:
        order = "订单号：PO-1；下单日期：2026年8月22日；客户：海川制造；产品：电机；数量：20台；交期：2026年9月10日；单价：5000；付款比例：30%"
        contract = "甲方：海川制造；乙方：智造云；产品：电机；数量：20台；交货日期：2026年9月10日；单价：5000；付款比例：30%；付款方式：验收付款；违约责任：延期赔偿；争议由法院管辖。"
        result = compare_order_contract(order, contract)
        self.assertTrue(result["consistent"])
        self.assertEqual(len(result["checks"]), 6)

    def test_difference_is_explainable(self) -> None:
        order = "订单号：PO-1；下单日期：2026年8月22日；客户：海川制造；产品：电机；数量：20台；交期：2026年9月10日"
        contract = "甲方：海川制造；产品：电机；数量：25台；交货日期：2026年9月12日；付款方式：验收付款。"
        result = compare_order_contract(order, contract)
        self.assertFalse(result["consistent"])
        self.assertEqual({item["field"] for item in result["differences"]}, {"数量", "交期"})
        self.assertTrue(result["requires_human_confirmation"])


if __name__ == "__main__":
    unittest.main()
