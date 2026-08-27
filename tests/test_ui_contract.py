# -*- coding: utf-8 -*-
from pathlib import Path
import unittest


class UiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).parents[1] / "ui" / "index.js").read_text(encoding="utf-8")

    def test_accepted_orders_sync_to_data_core(self) -> None:
        """跨应用数据契约：接受的订单必须同步统一数据中心 orders 实体（PRD 9/19.11）。"""
        self.assertIn("syncToDataCore", self.source)
        self.assertIn("/zhiyun-data-core/imports/orders/commit?data_mode=production", self.source)
        self.assertIn('localStorage.getItem("zhiyun_token")', self.source)


if __name__ == "__main__":
    unittest.main()
