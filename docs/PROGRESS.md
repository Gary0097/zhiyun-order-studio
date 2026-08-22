# 功能进度台账

| 版本 | 功能 | 状态 | 验收依据 |
|---|---|---|---|
| 0.5.2 | 合同导入、风险与一致性检查 | 已完成 | PR #5—#7、既有测试 |
| 0.6.0 | 真实订单输入、持久化、证据、审阅/撤销、JSON/CSV 导出 | 已完成 | `test_order_workflow.py`、`test_workflow_interfaces.py` |
| 0.6.1 | Workspace 私有库、表命名空间、Schema 版本和可恢复迁移 | 已完成 | `test_order_migrations.py` |

v0.6.1 默认数据库位于当前 QwenPaw Workspace，`ORDER_STUDIO_DB` 仅保留为运维覆盖。升级会保留 v0.6.0 的 Project、Run、Step、Artifact、Review、客户原文和证据，不接触 Data Core 公共业务表。
