# Zhiyun Order Studio

独立 PawApp。v0.6.0 将用户真实微信、邮件或 OCR 订单原文保存为 SQLite 项目，并为每次处理保存 Run、Step、带来源证据的 Artifact 和 Review。具名审阅人可接受、撤销，并在接受状态导出 JSON/CSV；不会使用写死订单或自动提交业务数据。合同导入、风险初筛与一致性验证能力继续保留。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/order_workflow.py backend/template_engine.py backend/contract_engine.py backend/document_parser.py backend/comparison_engine.py
node --check ui/index.js
```
