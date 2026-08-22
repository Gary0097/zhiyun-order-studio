# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


class WorkflowInterfaceTests(unittest.TestCase):
    def test_http_and_agent_interfaces_are_registered(self) -> None:
        source = (Path(__file__).parents[1] / "backend" / "main.py").read_text(encoding="utf-8")
        for route in ['@router.post("/projects")', '@router.get("/projects/{project_id}")',
                      '@router.post("/projects/{project_id}/reviews")', '@router.get("/projects/{project_id}/export")',
                      '@router.post("/exceptions")', '@router.post("/exceptions/{case_id}/reviews")',
                      '@router.post("/exceptions/{case_id}/retry")', '@router.get("/exceptions/{case_id}/export")']:
            self.assertIn(route, source)
        self.assertIn('tool_name="run_customer_order_workflow"', source)
        self.assertIn('tool_name="run_order_exception_workflow"', source)

    def test_frontend_uses_real_blank_input_and_review_controls(self) -> None:
        source = (Path(__file__).parents[1] / "ui" / "index.js").read_text(encoding="utf-8")
        self.assertIn('React.useState("")', source)
        self.assertNotIn("PO-20260822-01", source)
        for label in ["接受", "撤销", "导出 JSON", "导出 CSV", "创建异常处理方案", "接受异常方案", "重试/恢复", "导出异常方案"]:
            self.assertIn(label, source)


if __name__ == "__main__":
    unittest.main()
