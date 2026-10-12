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
CREATE TABLE IF NOT EXISTS leader_faces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    embedding BLOB NOT NULL,
    source_photo TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_user TEXT NOT NULL,
    source_host TEXT,
    ts REAL NOT NULL,
    snapshot TEXT
);
"""


class Database:
    """线程安全的本地数据库（多线程经锁串行访问）。"""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.RLock()
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

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

    # ---------- 领导特征 ----------
    def add_leader_face(self, embedding: np.ndarray, source_photo: str) -> int:
        blob = embedding.astype(np.float32).tobytes()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO leader_faces (embedding, source_photo, created_at) VALUES (?, ?, ?)",
                (blob, source_photo, time.time()),
            )
            self._conn.commit()
        return cur.lastrowid

    def list_leader_faces(self):
        """返回 [(id, source_photo, created_at), ...]。"""
        with self._lock:
            return self._conn.execute(
                "SELECT id, source_photo, created_at FROM leader_faces ORDER BY id"
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
        """返回特征向量列表 [np.ndarray, ...]。"""
        with self._lock:
            rows = self._conn.execute(
                "SELECT embedding FROM leader_faces"
            ).fetchall()
        return [np.frombuffer(r[0], dtype=np.float32) for r in rows]

    # ---------- 报警记录 ----------
    def add_alert(self, source_user: str, source_host: str, ts: float, snapshot=None) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO alerts (source_user, source_host, ts, snapshot) VALUES (?, ?, ?, ?)",
                (source_user, source_host, ts, snapshot),
            )
            self._conn.commit()
        return cur.lastrowid

    def recent_alerts(self, limit: int = 200):
        """返回 [(id, source_user, source_host, ts, snapshot), ...]，按时间倒序。"""
        with self._lock:
            return self._conn.execute(
                "SELECT id, source_user, source_host, ts, snapshot FROM alerts "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    def clear_alerts(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM alerts")
            self._conn.commit()
