import sqlite3
import threading
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS areas (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    sort_order  INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    notes        TEXT DEFAULT '',
    area_id      TEXT REFERENCES areas(id) ON DELETE SET NULL,
    status       TEXT DEFAULT 'active',
    deadline     TEXT,
    sort_order   INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS tags (
    id    TEXT PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#888888'
);

CREATE TABLE IF NOT EXISTS tasks (
    id             TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    notes          TEXT DEFAULT '',
    status         TEXT DEFAULT 'inbox',
    schedule       TEXT DEFAULT 'inbox',
    due_date       TEXT,
    scheduled_date TEXT,
    project_id     TEXT REFERENCES projects(id) ON DELETE SET NULL,
    area_id        TEXT REFERENCES areas(id) ON DELETE SET NULL,
    sort_order     INTEGER DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now')),
    completed_at   TEXT
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id         TEXT PRIMARY KEY,
    task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    is_done    INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id  TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);
"""

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
    title, notes, content=tasks, content_rowid=rowid
);

CREATE TRIGGER IF NOT EXISTS tasks_ai AFTER INSERT ON tasks BEGIN
    INSERT INTO tasks_fts(rowid, title, notes) VALUES (new.rowid, new.title, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS tasks_ad AFTER DELETE ON tasks BEGIN
    INSERT INTO tasks_fts(tasks_fts, rowid, title, notes) VALUES('delete', old.rowid, old.title, old.notes);
END;

CREATE TRIGGER IF NOT EXISTS tasks_au AFTER UPDATE ON tasks BEGIN
    INSERT INTO tasks_fts(tasks_fts, rowid, title, notes) VALUES('delete', old.rowid, old.title, old.notes);
    INSERT INTO tasks_fts(rowid, title, notes) VALUES (new.rowid, new.title, new.notes);
END;
"""


class Database:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        cursor = self._conn.cursor()
        version = cursor.execute("PRAGMA user_version").fetchone()[0]
        if version < SCHEMA_VERSION:
            cursor.executescript(SCHEMA_SQL)
            cursor.executescript(FTS_SQL)
            cursor.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            self._conn.commit()

    def execute(self, sql: str, params=None):
        with self._lock:
            cursor = self._conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self._conn.commit()
            return cursor

    def executemany(self, sql: str, params_list):
        with self._lock:
            cursor = self._conn.cursor()
            cursor.executemany(sql, params_list)
            self._conn.commit()
            return cursor

    def fetchone(self, sql: str, params=None):
        with self._lock:
            cursor = self._conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchone()

    def fetchall(self, sql: str, params=None):
        with self._lock:
            cursor = self._conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()

    def close(self):
        self._conn.close()
