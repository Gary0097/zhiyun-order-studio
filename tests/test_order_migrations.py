# -*- coding: utf-8 -*-

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend.order_workflow import PREFIX, SCHEMA_VERSION, VERSION_TABLE, OrderWorkflowStore


def create_v060_database(path: Path) -> None:
    evidence = {"order": {"order_no": "OLD-1"}, "source_text": "客户原始输入", "evidence": [{"field": "order_no", "source": "订单号：OLD-1"}]}
    with sqlite3.connect(str(path)) as db:
        db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, source_channel TEXT NOT NULL, source_text TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE runs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), status TEXT NOT NULL, error_code TEXT, error_message TEXT, created_at TEXT NOT NULL, completed_at TEXT);
            CREATE TABLE steps (id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), name TEXT NOT NULL, status TEXT NOT NULL, detail TEXT, position INTEGER NOT NULL);
            CREATE TABLE artifacts (id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), kind TEXT NOT NULL, content_json TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE reviews (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), artifact_id TEXT NOT NULL REFERENCES artifacts(id), action TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL);
        """)
        db.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?)", ("p1", "旧项目", "wechat", "客户原始输入", "accepted", "t", "t"))
        db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?,?)", ("r1", "p1", "pending_review", None, None, "t", "t"))
        db.execute("INSERT INTO steps VALUES (?,?,?,?,?,?)", ("s1", "r1", "extract_order", "completed", "旧步骤", 1))
        db.execute("INSERT INTO artifacts VALUES (?,?,?,?,?)", ("a1", "r1", "formatted_order", json.dumps(evidence, ensure_ascii=False), "t"))
        db.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?)", ("v1", "p1", "a1", "accept", "旧审阅人", None, "t"))


class FailingMigrationStore(OrderWorkflowStore):
    def _migration_hook(self, stage: str) -> None:
        if stage == "renamed:runs":
            raise RuntimeError("injected migration failure")


class OrderMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "orders.db"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_populated_v060_upgrade_preserves_every_entity_and_evidence(self) -> None:
        create_v060_database(self.path)
        store = OrderWorkflowStore(self.path)
        project = store.get_project("p1")
        self.assertEqual(project["source_text"], "客户原始输入")
        self.assertEqual(project["runs"][0]["steps"][0]["id"], "s1")
        self.assertEqual(project["runs"][0]["artifacts"][0]["content"]["evidence"][0]["source"], "订单号：OLD-1")
        self.assertEqual(project["reviews"][0]["reviewer"], "旧审阅人")
        self.assertTrue(self.path.with_suffix(".db.pre-v1.bak").exists())
        with sqlite3.connect(str(self.path)) as db:
            names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn("projects", names)
            self.assertIn(PREFIX + "projects", names)
            self.assertEqual(db.execute(f"SELECT version FROM {VERSION_TABLE}").fetchone()[0], SCHEMA_VERSION)

    def test_repeated_start_and_migration_are_idempotent(self) -> None:
        first = OrderWorkflowStore(self.path)
        project = first.create_project("客户：甲公司", "email")
        second = OrderWorkflowStore(self.path)
        second.migrate()
        second.migrate()
        self.assertEqual(second.get_project(project["id"])["source_text"], "客户：甲公司")
        with sqlite3.connect(str(self.path)) as db:
            self.assertEqual(db.execute(f"SELECT count(*) FROM {VERSION_TABLE}").fetchone()[0], 1)

    def test_mid_migration_failure_rolls_back_and_backup_can_recover(self) -> None:
        create_v060_database(self.path)
        with self.assertRaisesRegex(RuntimeError, "injected"):
            FailingMigrationStore(self.path)
        with sqlite3.connect(str(self.path)) as db:
            names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("projects", names)
            self.assertNotIn(PREFIX + "projects", names)
            self.assertEqual(db.execute("SELECT source_text FROM projects WHERE id='p1'").fetchone()[0], "客户原始输入")
        backup = self.path.with_suffix(".db.pre-v1.bak")
        with sqlite3.connect(str(backup)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM reviews").fetchone()[0], 1)
        self.assertEqual(OrderWorkflowStore(self.path).get_project("p1")["id"], "p1")

    def test_connections_are_closed_for_windows_file_operations(self) -> None:
        OrderWorkflowStore(self.path).migrate()
        moved = self.path.with_name("moved.db")
        os.replace(self.path, moved)
        self.assertTrue(moved.exists())
        self.assertEqual(OrderWorkflowStore(moved).path, moved)

    def test_linux_directory_permission_error_is_explicit(self) -> None:
        with mock.patch.object(Path, "mkdir", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(OSError, "Workspace 数据目录"):
                OrderWorkflowStore(self.path)

    def test_default_database_is_inside_current_workspace(self) -> None:
        workspace = Path(self.temp.name) / "workspace"
        with mock.patch.dict(os.environ, {"QWENPAW_WORKSPACE": str(workspace)}, clear=False):
            with mock.patch.dict(os.environ, {"ORDER_STUDIO_DB": ""}, clear=False):
                store = OrderWorkflowStore()
        self.assertTrue(store.path.is_relative_to(workspace))

    def test_old_home_database_is_copied_not_modified_into_workspace(self) -> None:
        fake_home = Path(self.temp.name) / "home"
        legacy = fake_home / ".zhiyun-order-studio" / "orders.db"
        legacy.parent.mkdir(parents=True)
        create_v060_database(legacy)
        workspace = Path(self.temp.name) / "workspace"
        with mock.patch.object(Path, "home", return_value=fake_home):
            with mock.patch.dict(os.environ, {"QWENPAW_WORKSPACE": str(workspace), "ORDER_STUDIO_DB": ""}, clear=False):
                store = OrderWorkflowStore()
        self.assertEqual(store.get_project("p1")["source_text"], "客户原始输入")
        with sqlite3.connect(str(legacy)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM projects").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
