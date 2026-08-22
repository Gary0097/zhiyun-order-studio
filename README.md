# Zhiyun Order Studio

独立 PawApp。v0.7.0 在真实订单、合同和一致性验证之上补齐异常处理工作台：持久化异常类别、证据、处理路径和回复话术，允许具名接受/驳回、重试恢复、复用数据库中的真实已解决案例，并只在接受后导出。不会使用写死订单、虚构历史案例或自动提交业务数据。

## 验证

```bash
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/order_parser.py backend/order_workflow.py backend/template_engine.py backend/contract_engine.py backend/document_parser.py backend/comparison_engine.py
node --check ui/index.js
```
