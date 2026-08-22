# Zhiyun Order Studio

独立 PawApp。v0.2.0 完成 PRD #7 的文本订单格式化与确认入库闭环：从微信、邮件或 OCR 结果文本中提取订单号、下单日期、客户、产品、数量和交期，保留逐字段原文证据；用户可编辑补充字段，确认后写入 Data Core 真实订单批次。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py
node --check ui/index.js
```
