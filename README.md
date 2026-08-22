# Zhiyun Order Studio

独立 PawApp。v0.4.0 在订单格式化和模板适配基础上推进 PRD #9：从合同文本提取双方、金额、付款、交付、违约和争议条款，保留原文证据，识别空白项、缺失条款和高风险表述，并给出可执行的修改建议。所有结果必须人工确认，且不构成法律意见。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/template_engine.py backend/contract_engine.py
node --check ui/index.js
```
