"""UDP 广播发送：定时心跳 + 报警广播。"""
import socket
import time

from PySide6.QtCore import QObject, QTimer

import config
from network import protocol
from network.protocol import AlertMsg, HeartbeatMsg


class Broadcaster(QObject):
    """负责所有出站 UDP 消息。"""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self._ctx = ctx  # 提供 user / host / role
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._timer = QTimer(self)
        self._timer.setInterval(config.HEARTBEAT_INTERVAL * 1000)
        self._timer.timeout.connect(self._send_heartbeat)

    def start(self):
        """启动心跳（立即发送一次 + 定时重发）。"""
        self._send_heartbeat()
        self._timer.start()

    def send_alert(self):
        """广播领导识别报警。"""
        self._send(AlertMsg(self._ctx.user, self._ctx.host, time.time()))

    def stop(self):
        self._timer.stop()
        try:
            self._sock.close()
        except OSError:
            pass

    # ---------- 内部 ----------
    def _send_heartbeat(self):
        self._send(HeartbeatMsg(self._ctx.user, self._ctx.host, self._ctx.role()))

    def _send(self, msg):
        try:
            self._sock.sendto(
                protocol.encode(msg), (config.BROADCAST_ADDR, config.UDP_PORT)
            )
        except OSError:
            pass  # 广播发送失败不影响主流程，下个周期重试
