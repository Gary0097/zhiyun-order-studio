# 智造云智能订单中心

独立 PawApp。v0.7.1 增加完整中文标题、页面内功能引导和使用说明；在真实订单、合同和一致性验证之上提供异常处理工作台。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/order_workflow.py backend/template_engine.py backend/contract_engine.py backend/document_parser.py backend/comparison_engine.py
node --check ui/index.js
```
