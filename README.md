# Zhiyun Order Studio

独立 PawApp。v0.1.0 完成 PRD #7 的文本订单格式化第一阶段：从微信、邮件或 OCR 结果文本中提取客户、产品、数量和交期，保留逐字段原文证据，缺失字段不猜测，所有结果必须人工确认后才能进入业务流程。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py
node --check ui/index.js
```
