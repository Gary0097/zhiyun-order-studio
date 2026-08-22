# Order Studio 产品需求

## v0.6 客户订单自动格式化闭环

用户粘贴真实微信、邮件或 OCR 结果，系统原样保存来源并创建 Project、Run、Step 与 Artifact。字段提取不得臆造，Artifact 必须携带逐字段原文证据；缺字段进入 `needs_input`，解析失败进入 `parse_failed`，存储不可用由接口返回 503。

产物只能由具名审阅人接受；人工修订记录为审阅证据。接受后可导出 JSON/CSV，撤销后立即禁止导出。任何操作都不得自动合并代码或自动提交业务订单。

## v0.6.1 数据安全整改

默认数据库必须位于当前 QwenPaw Workspace；`ORDER_STUDIO_DB` 仅为运维覆盖。所有私有表使用 `zhiyun-order-studio_*` 命名空间，不得读写 Data Core 公共业务表。升级必须先备份，再通过向前、幂等的事务 Migration 保存 v0.6.0 全部数据。

回滚不得删除整个数据库：代码使用 `git revert`；数据先保留升级前备份，再按 Project/Run 或迁移批次恢复。升级后新建的数据必须保留并由人工决定如何重放，不得以旧库覆盖整个新库。
