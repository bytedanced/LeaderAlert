"""UDP 消息定义与编解码。

两类消息（UTF-8 JSON）：
- heartbeat：心跳，维护在线列表
- alert：领导识别报警
"""
import json
import time

MSG_HEARTBEAT = "heartbeat"
MSG_ALERT = "alert"


class HeartbeatMsg:
    """心跳消息：身份 + 角色声明。"""

    def __init__(self, user, host, role, ts=None):
        self.user = user
        self.host = host
        self.role = role
        self.ts = ts if ts is not None else time.time()

    def to_dict(self):
        return {
            "type": MSG_HEARTBEAT,
            "user": self.user,
            "host": self.host,
            "role": self.role,
            "ts": self.ts,
        }

    @staticmethod
    def from_dict(d):
        return HeartbeatMsg(d.get("user", ""), d.get("host", ""), d.get("role", ""), d.get("ts"))


class AlertMsg:
    """报警消息：识别到目标，由识别端广播。"""

    def __init__(self, user, host, ts=None, target=""):
        self.user = user
        self.host = host
        self.ts = ts if ts is not None else time.time()
        self.target = target or ""

    def to_dict(self):
        return {
            "type": MSG_ALERT,
            "user": self.user,
            "host": self.host,
            "ts": self.ts,
            "target": self.target,
        }

    @staticmethod
    def from_dict(d):
        return AlertMsg(d.get("user", ""), d.get("host", ""), d.get("ts"), d.get("target", ""))


def encode(msg) -> bytes:
    """把 HeartbeatMsg / AlertMsg 编码为 UDP 载荷。"""
    return json.dumps(msg.to_dict(), ensure_ascii=False).encode("utf-8")


def decode(data: bytes):
    """把 UDP 载荷解码为消息对象；无效消息返回 None。"""
    try:
        d = json.loads(data.decode("utf-8"))
        msg_type = d.get("type")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    if msg_type == MSG_HEARTBEAT:
        return HeartbeatMsg.from_dict(d)
    if msg_type == MSG_ALERT:
        return AlertMsg.from_dict(d)
    return None
