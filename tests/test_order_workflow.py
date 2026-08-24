# -*- coding: utf-8 -*-

import json
import tempfile
import unittest
from pathlib import Path

from backend.order_workflow import OrderWorkflowStore


COMPLETE = "订单号：PO-9；下单日期：2026年8月22日；客户：海川制造；产品：伺服电机；数量：20台；交期：2026年9月10日"


class OrderWorkflowTests(unittest.TestCase):
    def test_simulation_channel_is_preserved(self) -> None:
        project = self.store.create_project(
            "订单号 A100 客户 测试客户 产品 电机 数量 2 下单日期 2026-08-01 承诺交期 2026-08-30",
            "simulation",
        )
        self.assertEqual(project["source_channel"], "simulation")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = OrderWorkflowStore(Path(self.temp.name) / "workflow.db")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_project_run_step_artifact_and_evidence_are_persisted(self) -> None:
        project = self.store.create_project(COMPLETE, "wechat", "微信订单")
        self.assertEqual(project["status"], "pending_review")
        self.assertEqual(project["source_text"], COMPLETE)
        self.assertEqual(project["runs"][0]["steps"][0]["status"], "completed")
        artifact = project["runs"][0]["artifacts"][0]
        self.assertEqual(artifact["kind"], "formatted_order")
        self.assertTrue(artifact["content"]["evidence"])
        reopened = OrderWorkflowStore(Path(self.temp.name) / "workflow.db")
        self.assertEqual(reopened.get_project(project["id"])["id"], project["id"])

    def test_missing_fields_have_explicit_status_and_can_be_review_completed(self) -> None:
        project = self.store.create_project("客户：海川制造，要20台", "email")
        self.assertEqual(project["status"], "needs_input")
        self.assertEqual(project["runs"][0]["error_code"], "missing_fields")
        order = {"order_no":"PO-10", "customer_name":"海川制造", "product_name":"电机", "quantity":20,
                 "unit":"台", "promised_date":"2026-09-10", "order_date":"2026-08-22", "unit_price":None,
                 "payment_ratio":None, "status":"待排产", "progress":0, "source_text":"客户：海川制造，要20台"}
        accepted = self.store.review(project["id"], "accept", "王审核", order=order)
        self.assertEqual(accepted["status"], "accepted")
        self.assertTrue(any(e.get("kind") == "reviewer_input" for e in accepted["runs"][0]["artifacts"][0]["content"]["evidence"]))

    def test_accept_revoke_and_export_gate(self) -> None:
        project = self.store.create_project(COMPLETE, "ocr")
        with self.assertRaisesRegex(ValueError, "已接受"):
            self.store.export(project["id"], "json")
        order = project["runs"][0]["artifacts"][0]["content"]["order"]
        accepted = self.store.review(project["id"], "accept", "reviewer", order=order)
        content, media = self.store.export(project["id"], "json")
        self.assertEqual(media, "application/json")
        self.assertEqual(json.loads(content)["project_id"], project["id"])
        csv_content, csv_media = self.store.export(project["id"], "csv")
        self.assertEqual(csv_media, "text/csv")
        self.assertIn("order_no", csv_content)
        revoked = self.store.review(accepted["id"], "revoke", "reviewer")
        self.assertEqual(revoked["status"], "pending_review")

    def test_empty_and_invalid_channel_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            self.store.create_project("  ", "wechat")
        with self.assertRaisesRegex(ValueError, "来源"):
            self.store.create_project(COMPLETE, "demo")

    def test_unrecognizable_input_has_parse_failed_status(self) -> None:
        project = self.store.create_project("这是一段无法识别为订单的消息", "wechat")
        self.assertEqual(project["status"], "parse_failed")
        self.assertEqual(project["runs"][0]["error_code"], "parse_failed")
        self.assertEqual(project["runs"][0]["steps"][0]["status"], "failed")

    def test_database_can_be_removed_immediately_after_use_on_windows(self) -> None:
        database = Path(self.temp.name) / "workflow.db"
        self.store.create_project(COMPLETE, "email")
        database.unlink()
        self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
