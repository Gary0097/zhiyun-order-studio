# Zhiyun Order Studio

独立 PawApp。v0.6.1 将用户真实微信、邮件或 OCR 订单原文保存到当前 QwenPaw Workspace 内的私有 SQLite 数据库，并为每次处理保存 Run、Step、带来源证据的 Artifact 和 Review。私有表使用 `zhiyun-order-studio_*` 命名空间；具名审阅人可接受、撤销，并在接受状态导出 JSON/CSV。合同导入、风险初筛与一致性验证能力继续保留。

默认数据库为当前 Workspace 下的 `.qwenpaw/apps/zhiyun-order-studio/orders.db`；`QWENPAW_WORKSPACE`（或 `QWENPAW_WORKSPACE_DIR`）用于定位 Workspace，`ORDER_STUDIO_DB` 仅作为运维覆盖。首次升级会复制旧版 `$HOME/.zhiyun-order-studio/orders.db`（不修改旧文件），创建升级前备份，再以事务方式迁移数据。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/order_workflow.py backend/template_engine.py backend/contract_engine.py backend/document_parser.py backend/comparison_engine.py
node --check ui/index.js
```
