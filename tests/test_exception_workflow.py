# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from pathlib import Path

from backend.exception_engine import build_exception_recommendation
from backend.order_workflow import OrderWorkflowStore


ORDER = "订单号：PO-11；下单日期：2026年8月22日；客户：海川制造；产品：伺服电机；数量：20台；交期：2026年9月10日；单价：100元；付款比例：30%"
CONTRACT = "合同编号 HT-11。甲方：海川制造。产品：伺服电机。数量：25台。交期：2026年9月20日。单价：110元。预付款50%。"


class ExceptionWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workflow.db"
        self.store = OrderWorkflowStore(self.database)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_recommendation_uses_order_contract_evidence(self) -> None:
        result = build_exception_recommendation(ORDER, CONTRACT)
        self.assertEqual(result["status"], "pending_review")
        self.assertIn("数量", result["categories"])
        self.assertIn("交期", result["categories"])
        self.assertTrue(result["comparison"]["differences"])
        self.assertTrue(all(item["requires_human_confirmation"] for item in result["recommendations"]))

    def test_accept_export_retry_and_history_similarity(self) -> None:
        case = self.store.create_exception(ORDER, CONTRACT)
        with self.assertRaisesRegex(ValueError, "已接受"):
            self.store.export_exception(case["id"])
        accepted = self.store.review_exception(case["id"], "accept", "王审核", "复核 → 双方确认", "请确认数量和交期")
        self.assertEqual(accepted["status"], "accepted")
        exported, media = self.store.export_exception(case["id"])
        self.assertEqual(media, "application/json")
        self.assertEqual(json.loads(exported)["reviews"][-1]["reviewer"], "王审核")

        similar = self.store.create_exception(ORDER.replace("PO-11", "PO-12"), CONTRACT)
        self.assertEqual(similar["recommendation"]["similar_resolved_cases"][0]["case_id"], case["id"])
        retried = self.store.retry_exception(similar["id"])
        self.assertEqual(retried["retry_count"], 1)
        self.assertEqual(retried["status"], "pending_review")

    def test_rejects_incomplete_acceptance_and_releases_windows_database(self) -> None:
        case = self.store.create_exception(ORDER, CONTRACT)
        with self.assertRaisesRegex(ValueError, "处理路径"):
            self.store.review_exception(case["id"], "accept", "王审核")
        self.store.review_exception(case["id"], "reject", "王审核", note="证据不足")
        self.database.unlink()
        self.assertFalse(self.database.exists())


if __name__ == "__main__":
    unittest.main()
