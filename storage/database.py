"""SQLite 存储：身份、设置、领导特征、报警记录。"""
import os
import sqlite3
import threading
import time

import numpy as np

_SCHEMA = """
CREATE TABLE IF NOT EXISTS identity (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    user TEXT NOT NULL,
    host TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS leader_faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    embedding BLOB NOT NULL,
    source_photo TEXT,
    target_id INTEGER,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_user TEXT NOT NULL,
    source_host TEXT,
    ts REAL NOT NULL,
    target TEXT,
    snapshot TEXT
);
"""


def _migrate(conn):
    """旧库迁移：leader_faces 加 target_id 归入「默认」目标；alerts 加 target 列。"""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(leader_faces)")]
    if "target_id" not in cols:
        conn.execute("ALTER TABLE leader_faces ADD COLUMN target_id INTEGER")
    orphan = conn.execute(
        "SELECT COUNT(*) FROM leader_faces WHERE target_id IS NULL"
    ).fetchone()[0]
    if orphan > 0:
        cur = conn.execute(
            "INSERT INTO targets (name, created_at) VALUES ('默认', ?)", (time.time(),)
        )
        conn.execute("UPDATE leader_faces SET target_id = ?", (cur.lastrowid,))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(alerts)")]
    if "target" not in cols:
        conn.execute("ALTER TABLE alerts ADD COLUMN target TEXT")
    conn.commit()


class Database:
    """线程安全的本地数据库（多线程经锁串行访问）。"""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.RLock()
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
            _migrate(self._conn)

    # ---------- 身份 ----------
    def get_identity(self):
        """返回 (user, host) 元组，未设置时返回 None。"""
        with self._lock:
            row = self._conn.execute(
                "SELECT user, host FROM identity WHERE id = 1"
            ).fetchone()
        return (row[0], row[1]) if row else None

    def set_identity(self, user: str, host: str = None) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM identity")
            self._conn.execute(
                "INSERT INTO identity (id, user, host, created_at) VALUES (1, ?, ?, ?)",
                (user, host, time.time()),
            )
            self._conn.commit()

    # ---------- 设置 ----------
    def set_setting(self, key: str, value) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
            self._conn.commit()

    def get_str(self, key: str, default=None):
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        if row is None or row[0] is None:
            return default
        return row[0] if row[0] else default

    def get_int(self, key: str, default: int) -> int:
        v = self.get_str(key, None)
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float) -> float:
        v = self.get_str(key, None)
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # ---------- 目标（牛）管理 ----------
    def list_targets(self):
        """返回 [(id, name, created_at), ...]。"""
        with self._lock:
            return self._conn.execute(
                "SELECT id, name, created_at FROM targets ORDER BY id"
            ).fetchall()

    def count_targets(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM targets").fetchone()
        return row[0]

    def add_target(self, name: str) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO targets (name, created_at) VALUES (?, ?)",
                (name, time.time()),
            )
            self._conn.commit()
        return cur.lastrowid

    def rename_target(self, target_id: int, name: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE targets SET name = ? WHERE id = ?", (name, target_id)
            )
            self._conn.commit()

    def delete_target(self, target_id: int):
        """删除目标及其全部特征，返回被删照片路径列表（供调用方清理文件）。"""
        with self._lock:
            photos = [
                r[0]
                for r in self._conn.execute(
                    "SELECT source_photo FROM leader_faces WHERE target_id = ?",
                    (target_id,),
                )
                if r[0]
            ]
            self._conn.execute(
                "DELETE FROM leader_faces WHERE target_id = ?", (target_id,)
            )
            self._conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))
            self._conn.commit()
        return photos

    # ---------- 领导特征 ----------
    def add_leader_face(self, embedding: np.ndarray, source_photo: str, target_id: int) -> int:
        blob = embedding.astype(np.float32).tobytes()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO leader_faces (embedding, source_photo, target_id, created_at) "
                "VALUES (?, ?, ?, ?)",
                (blob, source_photo, target_id, time.time()),
            )
            self._conn.commit()
        return cur.lastrowid

    def list_leader_faces(self, target_id: int = None):
        """返回指定目标的 [(id, source_photo, created_at), ...]；target_id 为 None 时返回全部。"""
        with self._lock:
            if target_id is None:
                return self._conn.execute(
                    "SELECT id, source_photo, created_at FROM leader_faces ORDER BY id"
                ).fetchall()
            return self._conn.execute(
                "SELECT id, source_photo, created_at FROM leader_faces "
                "WHERE target_id = ? ORDER BY id",
                (target_id,),
            ).fetchall()

    def count_leader_faces(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM leader_faces").fetchone()
        return row[0]

    def delete_leader_face(self, face_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM leader_faces WHERE id = ?", (face_id,))
            self._conn.commit()

    def load_leader_embeddings(self):
        """返回 [(特征向量, 目标名), ...]。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT f.embedding, COALESCE(t.name, '未知') "
                "FROM leader_faces f LEFT JOIN targets t ON t.id = f.target_id"
            ).fetchall()
        return [(np.frombuffer(r[0], dtype=np.float32), r[1]) for r in rows]

    # ---------- 报警记录 ----------
    def add_alert(self, source_user: str, source_host: str, ts: float, snapshot=None, target: str = None) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO alerts (source_user, source_host, ts, target, snapshot) "
                "VALUES (?, ?, ?, ?, ?)",
                (source_user, source_host, ts, target, snapshot),
            )
            self._conn.commit()
        return cur.lastrowid

    def recent_alerts(self, limit: int = 200):
        """返回 [(id, source_user, source_host, ts, target, snapshot), ...]，按时间倒序。"""
        with self._lock:
            return self._conn.execute(
                "SELECT id, source_user, source_host, ts, target, snapshot FROM alerts "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def clear_alerts(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM alerts")
            self._conn.commit()
