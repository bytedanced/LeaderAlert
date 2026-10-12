"""UDP 接收线程：监听广播，转发心跳/报警信号。"""
import socket

from PySide6.QtCore import QThread, Signal

from network import protocol
from network.protocol import AlertMsg, HeartbeatMsg


class ListenerThread(QThread):
    heartbeat_received = Signal(object)  # HeartbeatMsg
    alert_received = Signal(object)      # AlertMsg
    bind_failed = Signal(str)            # 端口绑定失败（如本机多实例未复用）

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self._port = port
        self._stop = False

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 允许本机多实例共用端口（Windows 下广播包会送达所有绑定者）
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            sock.bind(("", self._port))
        except OSError as e:
            self.bind_failed.emit(str(e))
            sock.close()
            return
        sock.settimeout(0.5)
        while not self._stop:
            try:
                data, _addr = sock.recvfrom(65536)
            except socket.timeout:
                continue
            except OSError:
                break
            msg = protocol.decode(data)
            if isinstance(msg, HeartbeatMsg):
                self.heartbeat_received.emit(msg)
            elif isinstance(msg, AlertMsg):
                self.alert_received.emit(msg)
        sock.close()

    def stop(self):
        self._stop = True
        self.wait(3000)
