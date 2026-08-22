# Order Studio 升级与恢复手册

## 升级

1. 停止 Order Studio 写入并记录待升级 commit。
2. 启动 v0.6.1。程序在迁移旧表前使用 SQLite Backup API 生成同目录 `orders.db.pre-v1.bak`。
3. Migration 在单个 `BEGIN IMMEDIATE` 事务中执行；Schema 版本写入 `zhiyun-order-studio_schema_versions` 后才提交。
4. 验证 Project、Run、Step、Artifact、Review 数量、客户原文、证据和 `PRAGMA foreign_key_check`。

旧版 home 数据库只会被复制到 Workspace，源文件不会被修改。备份与旧文件都应依照客户数据保留策略保护，不得上传到代码仓库。

## 失败恢复

Migration 异常会回滚整个事务，原表和原记录保持可用；修复环境后可幂等重试。若 SQLite 文件自身损坏，应先复制故障文件用于审计，再从 `orders.db.pre-v1.bak` 恢复到隔离位置，核验后以 Project/Run 为单位导回，不能直接覆盖仍包含升级后新数据的生产库。

## 代码与数据回滚

代码使用 `git revert <upgrade-commit-sha>`。数据不随 Git 回滚，不删除整个数据库。需要撤回迁移数据时，根据 Project ID、Run ID 和 Review 时间范围生成恢复清单，事务性恢复对应记录；已经在升级后创建的数据保留。任何恢复操作前再次制作 SQLite 在线备份，并记录操作者、时间、记录范围和校验结果。
