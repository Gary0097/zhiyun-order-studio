# 功能进度台账

| 版本 | 功能 | 状态 | 验收依据 |
|---|---|---|---|
| 0.5.2 | 合同导入、风险与一致性检查 | 已完成 | PR #5—#7、既有测试 |
| 0.6.0 | 真实订单输入、持久化、证据、审阅/撤销、JSON/CSV 导出 | 已完成 | `test_order_workflow.py`、`test_workflow_interfaces.py` |

v0.6.0 使用 Python 标准库 SQLite 与 `pathlib`，数据库位置可由 `ORDER_STUDIO_DB` 配置，兼容 Windows 与 Linux 路径。
