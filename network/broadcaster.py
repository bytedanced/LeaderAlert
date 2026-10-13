"""UDP 广播发送：定时心跳 + 报警广播。"""
import socket
import time

from PySide6.QtCore import QObject, QTimer

from network import protocol
from network.protocol import AlertMsg, HeartbeatMsg


class Broadcaster(QObject):
    """负责所有出站 UDP 消息；端口/广播地址/心跳间隔从数据库设置读取。"""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx  # 提供 user / host / role / db
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._timer = QTimer(self)
        self._timer.setInterval(ctx.heartbeat_interval() * 1000)
        self._timer.timeout.connect(self._send_heartbeat)

    def start(self):
        """启动心跳（立即发送一次 + 定时重发）。"""
        self._timer.setInterval(self._ctx.heartbeat_interval() * 1000)
        self._send_heartbeat()
        self._timer.start()

    def send_alert(self, target: str = ""):
        """广播目标识别报警，target 为命中的目标名。"""
        self._send(AlertMsg(self._ctx.user, self._ctx.host, time.time(), target))

    def stop(self):
        self._timer.stop()
        try:
            self._sock.close()
        except OSError:
            pass

    # ---------- 内部 ----------
    def _send_heartbeat(self):
        self._send(HeartbeatMsg(
            self._ctx.user, self._ctx.host, self._ctx.role(),
            sync_port=self._ctx.sync_port(),
        ))

    def _send(self, msg):
        payload = protocol.encode(msg)
        port = self._ctx.udp_port()
        for addr in self._ctx.broadcast_addrs():
            try:
                self._sock.sendto(payload, (addr, port))
            except OSError:
                pass  # 单个地址发送失败不影响其他地址，下个周期重试
