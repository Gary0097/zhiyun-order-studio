# -*- coding: utf-8 -*-
"""Persistent, auditable customer-order formatting workflow."""

from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .order_parser import parse_order_text
except ImportError:
    from order_parser import parse_order_text

CHANNELS = {"wechat", "email", "ocr"}
SCHEMA_VERSION = 1
PREFIX = "zhiyun-order-studio_"
TABLES = {name: f'"{PREFIX}{name}"' for name in ("projects", "runs", "steps", "artifacts", "reviews")}
VERSION_TABLE = f'"{PREFIX}schema_versions"'


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderWorkflowStore:
    """SQLite repository. Each transition is committed as one transaction."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("ORDER_STUDIO_DB")
        workspace = os.getenv("QWENPAW_WORKSPACE") or os.getenv("QWENPAW_WORKSPACE_DIR")
        workspace_path = Path(workspace) if workspace else Path.cwd()
        self.path = Path(configured) if configured else workspace_path / ".qwenpaw" / "apps" / "zhiyun-order-studio" / "orders.db"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OSError(f"无法创建 Order Studio Workspace 数据目录 {self.path.parent}: {exc}") from exc
        if not configured:
            self._import_v060_home_database()
        self.migrate()

    def _import_v060_home_database(self) -> None:
        """Copy the old v0.6.0 home database into Workspace once; never mutate it."""
        legacy = Path.home() / ".zhiyun-order-studio" / "orders.db"
        if self.path.exists() or not legacy.is_file() or legacy.resolve() == self.path.resolve():
            return
        temporary = self.path.with_suffix(self.path.suffix + ".importing")
        try:
            with closing(sqlite3.connect(str(legacy))) as source, closing(sqlite3.connect(str(temporary))) as destination:
                source.backup(destination)
            os.replace(temporary, self.path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _table_names(self, db: sqlite3.Connection) -> set[str]:
        return {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    def _migration_hook(self, stage: str) -> None:
        """Test/operations hook; raising rolls the entire migration back."""

    def _backup_legacy_database(self) -> Path:
        backup = self.path.with_suffix(self.path.suffix + ".pre-v1.bak")
        temporary = backup.with_suffix(backup.suffix + ".tmp")
        with closing(self._connect()) as source, closing(sqlite3.connect(str(temporary))) as destination:
            source.backup(destination)
        os.replace(temporary, backup)
        return backup

    def migrate(self) -> None:
        """Apply forward-only, transactional and idempotent schema migrations."""
        legacy = {"projects", "runs", "steps", "artifacts", "reviews"}
        with closing(self._connect()) as probe:
            names = self._table_names(probe)
        if names & legacy:
            self._backup_legacy_database()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute(f"CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
            names = self._table_names(db)
            for name in ("projects", "runs", "steps", "artifacts", "reviews"):
                target = f"{PREFIX}{name}"
                if name in names and target not in names:
                    db.execute(f'ALTER TABLE "{name}" RENAME TO "{target}"')
                    self._migration_hook(f"renamed:{name}")
                    names.remove(name)
                    names.add(target)
            self._create_schema(db)
            db.execute(f"INSERT OR IGNORE INTO {VERSION_TABLE} (version, applied_at) VALUES (?, ?)", (SCHEMA_VERSION, _now()))
            self._migration_hook("before_commit")
            if db.execute("PRAGMA foreign_key_check").fetchone():
                raise sqlite3.IntegrityError("迁移后外键完整性检查失败")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _create_schema(self, db: sqlite3.Connection) -> None:
        statements = [f"""CREATE TABLE IF NOT EXISTS {TABLES['projects']} (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, source_channel TEXT NOT NULL,
                    source_text TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )""", f"""CREATE TABLE IF NOT EXISTS {TABLES['runs']} (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES {TABLES['projects']}(id), status TEXT NOT NULL,
                    error_code TEXT, error_message TEXT, created_at TEXT NOT NULL, completed_at TEXT
                )""", f"""CREATE TABLE IF NOT EXISTS {TABLES['steps']} (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES {TABLES['runs']}(id), name TEXT NOT NULL,
                    status TEXT NOT NULL, detail TEXT, position INTEGER NOT NULL
                )""", f"""CREATE TABLE IF NOT EXISTS {TABLES['artifacts']} (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES {TABLES['runs']}(id), kind TEXT NOT NULL,
                    content_json TEXT NOT NULL, created_at TEXT NOT NULL
                )""", f"""CREATE TABLE IF NOT EXISTS {TABLES['reviews']} (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES {TABLES['projects']}(id), artifact_id TEXT NOT NULL REFERENCES {TABLES['artifacts']}(id),
                    action TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL
                )"""]
        for statement in statements:
            db.execute(statement)

    def create_project(self, source_text: str, source_channel: str, name: str | None = None) -> dict[str, Any]:
        source = source_text.strip()
        if not source:
            raise ValueError("客户订单原文不能为空")
        if source_channel not in CHANNELS:
            raise ValueError("来源必须是 wechat、email 或 ocr")
        project_id, run_id = str(uuid.uuid4()), str(uuid.uuid4())
        now = _now()
        with self._session() as db:
            db.execute(f"INSERT INTO {TABLES['projects']} VALUES (?,?,?,?,?,?,?)", (project_id, name or f"客户订单 {now[:10]}", source_channel, source, "processing", now, now))
            db.execute(f"INSERT INTO {TABLES['runs']} VALUES (?,?,?,?,?,?,?)", (run_id, project_id, "running", None, None, now, None))
            step_id = str(uuid.uuid4())
            db.execute(f"INSERT INTO {TABLES['steps']} VALUES (?,?,?,?,?,?)", (step_id, run_id, "extract_order", "running", "保留原始输入并提取字段", 1))
            try:
                result = parse_order_text(source)
                if not result["evidence"]:
                    raise ValueError("未识别到任何订单字段")
                status = "needs_input" if result["missing_fields"] else "pending_review"
                error_code = "missing_fields" if result["missing_fields"] else None
                artifact_id = str(uuid.uuid4())
                content = {"source_channel": source_channel, "source_text": source, **result}
                db.execute(f"INSERT INTO {TABLES['artifacts']} VALUES (?,?,?,?,?)", (artifact_id, run_id, "formatted_order", json.dumps(content, ensure_ascii=False), now))
                db.execute(f"UPDATE {TABLES['steps']} SET status=?, detail=? WHERE id=?", ("completed", "提取完成；所有已提取字段均附来源证据", step_id))
            except (ValueError, TypeError) as exc:
                status, error_code, artifact_id = "parse_failed", "parse_failed", None
                db.execute(f"UPDATE {TABLES['steps']} SET status=?, detail=? WHERE id=?", ("failed", str(exc), step_id))
            db.execute(f"UPDATE {TABLES['runs']} SET status=?, error_code=?, error_message=?, completed_at=? WHERE id=?", (status, error_code, "必填字段缺失" if error_code == "missing_fields" else ("无法解析输入" if error_code else None), now, run_id))
            db.execute(f"UPDATE {TABLES['projects']} SET status=?, updated_at=? WHERE id=?", (status, now, project_id))
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._session() as db:
            project = db.execute(f"SELECT * FROM {TABLES['projects']} WHERE id=?", (project_id,)).fetchone()
            if not project:
                raise KeyError(project_id)
            runs = []
            for run in db.execute(f"SELECT * FROM {TABLES['runs']} WHERE project_id=? ORDER BY created_at", (project_id,)):
                item = dict(run)
                item["steps"] = [dict(row) for row in db.execute(f"SELECT * FROM {TABLES['steps']} WHERE run_id=? ORDER BY position", (run["id"],))]
                item["artifacts"] = [{**dict(row), "content": json.loads(row["content_json"])} for row in db.execute(f"SELECT * FROM {TABLES['artifacts']} WHERE run_id=?", (run["id"],))]
                for artifact in item["artifacts"]:
                    artifact.pop("content_json")
                runs.append(item)
            reviews = [dict(row) for row in db.execute(f"SELECT * FROM {TABLES['reviews']} WHERE project_id=? ORDER BY created_at", (project_id,))]
            return {**dict(project), "runs": runs, "reviews": reviews}

    def review(self, project_id: str, action: str, reviewer: str, note: str | None = None, order: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in {"accept", "revoke"}:
            raise ValueError("审阅动作必须是 accept 或 revoke")
        if not reviewer.strip():
            raise ValueError("审阅人不能为空")
        project = self.get_project(project_id)
        artifacts = [a for run in project["runs"] for a in run["artifacts"]]
        if not artifacts:
            raise ValueError("没有可审阅的格式化结果")
        required = ["order_no", "customer_name", "product_name", "quantity", "order_date", "promised_date"]
        if action == "accept" and (not order or any(order.get(field) in (None, "") for field in required)):
            raise ValueError("必填字段缺失，不能接受")
        status, now = ("accepted" if action == "accept" else "pending_review"), _now()
        with self._session() as db:
            if action == "accept" and order:
                artifact_row = db.execute(f"SELECT content_json FROM {TABLES['artifacts']} WHERE id=?", (artifacts[-1]["id"],)).fetchone()
                content = json.loads(artifact_row["content_json"])
                for field, value in order.items():
                    if content["order"].get(field) != value:
                        content["evidence"].append({"field": field, "source": "人工审阅补充/修正", "kind": "reviewer_input"})
                content["order"] = order
                content["missing_fields"] = []
                content["ready_for_review"] = True
                db.execute(f"UPDATE {TABLES['artifacts']} SET content_json=? WHERE id=?", (json.dumps(content, ensure_ascii=False), artifacts[-1]["id"]))
            db.execute(f"INSERT INTO {TABLES['reviews']} VALUES (?,?,?,?,?,?,?)", (str(uuid.uuid4()), project_id, artifacts[-1]["id"], action, reviewer.strip(), note, now))
            db.execute(f"UPDATE {TABLES['projects']} SET status=?, updated_at=? WHERE id=?", (status, now, project_id))
        return self.get_project(project_id)

    def export(self, project_id: str, export_format: str) -> tuple[str, str]:
        project = self.get_project(project_id)
        if project["status"] != "accepted":
            raise ValueError("只有已接受的订单可以导出")
        artifact = project["runs"][-1]["artifacts"][-1]["content"]
        payload = artifact["order"]
        if export_format == "json":
            return json.dumps({"project_id": project_id, "source_channel": project["source_channel"], "order": payload, "evidence": artifact["evidence"]}, ensure_ascii=False, indent=2), "application/json"
        if export_format == "csv":
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=list(payload))
            writer.writeheader(); writer.writerow(payload)
            return "\ufeff" + stream.getvalue(), "text/csv"
        raise ValueError("导出格式必须是 json 或 csv")
