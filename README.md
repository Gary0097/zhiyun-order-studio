# Zhiyun Order Studio

独立 PawApp。v0.3.0 完成 PRD #7 的文本订单格式化与确认入库闭环，并推进 PRD #8：根据原始订单文本匹配标准、FOB出口、代工/OEM或促销订单模板，返回关键词依据、必填字段和处理步骤，所有推荐均需人工确认。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py
node --check ui/index.js
```
