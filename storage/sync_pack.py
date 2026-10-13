"""牛管理数据打包/导入：单 JSON（UTF-8），照片 base64 内联，无临时文件。

结构：
{
  "version": 1,
  "exported_by": "user@host",
  "exported_at": 1234567890.0,
  "targets": [
    {"name": "张三", "faces": [{"photo_b64": "...", "photo_ext": ".jpg", "embedding_b64": "..."}]}
  ]
}
"""
import base64
import json
import os
import time
import uuid

import numpy as np

from storage import paths

MANIFEST_VERSION = 1


def pack_targets(db, user: str, host: str) -> bytes:
    """把本地 targets + faces + 照片序列化为 JSON 字节。"""
    data = {
        "version": MANIFEST_VERSION,
        "exported_by": f"{user}@{host}",
        "exported_at": time.time(),
        "targets": [],
    }
    for tid, name, _created in db.list_targets():
        entry = {"name": name, "faces": []}
        for face_id, photo_path, _c in db.list_leader_faces(tid):
            emb = db.get_face_embedding(face_id)
            if emb is None:
                continue
            face = {
                "embedding_b64": base64.b64encode(
                    emb.astype(np.float32).tobytes()).decode("ascii"),
            }
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, "rb") as f:
                    face["photo_b64"] = base64.b64encode(f.read()).decode("ascii")
                face["photo_ext"] = os.path.splitext(photo_path)[1] or ".jpg"
            entry["faces"].append(face)
        data["targets"].append(entry)
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def list_conflicts(data: bytes, db) -> list:
    """返回数据包中与本地重名的目标名列表（供导入前让用户决策）。"""
    manifest = json.loads(data.decode("utf-8"))
    _check_version(manifest)
    local_names = {name for _id, name, _c in db.list_targets()}
    return [t["name"] for t in manifest["targets"] if t["name"] in local_names]


def import_targets(data: bytes, db, conflicts: dict = None) -> dict:
    """导入数据包。

    conflicts: {目标名: 'skip'/'overwrite'/'rename'}，未列出的重名目标默认 skip。
    返回按目标计数的统计。
    """
    conflicts = conflicts or {}
    manifest = json.loads(data.decode("utf-8"))
    _check_version(manifest)
    stats = {"imported": 0, "imported_faces": 0, "skipped": 0, "overwritten": 0, "renamed": 0}

    local_names = {name for _id, name, _c in db.list_targets()}
    for target in manifest["targets"]:
        name = target["name"]
        exists = name in local_names
        action = conflicts.get(name, "skip") if exists else "new"

        if exists and action == "skip":
            stats["skipped"] += 1
            continue
        if exists and action == "overwrite":
            _delete_target_by_name(db, name)
            local_names.discard(name)
            stats["overwritten"] += 1
        if exists and action == "rename":
            name = _unique_name(name, manifest.get("exported_by", "未知"), local_names)
            stats["renamed"] += 1

        target_id = db.add_target(name)
        local_names.add(name)
        stats["imported"] += 1
        for face in target["faces"]:
            photo_path = _save_photo(face)
            emb = np.frombuffer(
                base64.b64decode(face["embedding_b64"]), dtype=np.float32)
            db.add_leader_face(emb, photo_path, target_id)
            stats["imported_faces"] += 1
    return stats


# ---------- 内部 ----------
def _check_version(manifest):
    if manifest.get("version") != MANIFEST_VERSION:
        raise ValueError(f"不支持的数据版本：{manifest.get('version')}")


def _unique_name(name: str, source: str, local_names: set) -> str:
    """rename 后确保与本地不重名（循环加序号）。"""
    candidate = f"{name} (来自 {source})"
    i = 2
    while candidate in local_names:
        candidate = f"{name} (来自 {source}) {i}"
        i += 1
    return candidate


def _save_photo(face: dict) -> str:
    """把 base64 照片写到本地照片目录，返回路径；无照片返回空串。"""
    b64 = face.get("photo_b64")
    if not b64:
        return ""
    ext = face.get("photo_ext", ".jpg")
    photo_path = os.path.join(paths.leader_photos_dir(), f"{uuid.uuid4().hex}{ext}")
    with open(photo_path, "wb") as f:
        f.write(base64.b64decode(b64))
    return photo_path


def _delete_target_by_name(db, name: str):
    """删除本地同名目标及其照片文件。"""
    for tid, tname, _c in db.list_targets():
        if tname == name:
            for photo in db.delete_target(tid):
                try:
                    os.remove(photo)
                except OSError:
                    pass
            return
