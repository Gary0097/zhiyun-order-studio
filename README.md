# Zhiyun Order Studio

独立 PawApp。v0.5.0 支持本地导入 TXT、Markdown、DOCX 和文本型 PDF 合同，完成证据化风险初筛；同时对订单与合同的客户、产品、数量、交期、单价和付款比例执行一致性验证。扫描 PDF 仍需先 OCR，所有差异必须人工确认。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/template_engine.py backend/contract_engine.py backend/document_parser.py backend/comparison_engine.py
node --check ui/index.js
```
