"""TCP 数据同步服务端：响应「导出牛管理数据」请求，直发 JSON 字节（无临时文件）。"""
import socket
import threading

from PySide6.QtCore import QThread, Signal

from storage.sync_pack import pack_targets


class SyncServerThread(QThread):
    """后台 TCP 服务，随 AppContext 启动/停止。"""

    error_occurred = Signal(str)

    def __init__(self, ctx, port, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self._port = port
        self._stop = False
        self._sock = None

    def run(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.bind(("0.0.0.0", self._port))
            self._sock.listen(5)
            self._sock.settimeout(0.5)
        except OSError as e:
            self.error_occurred.emit(f"同步端口 {self._port} 绑定失败：{e}")
            self._sock.close()
            return

        while not self._stop:
            try:
                client, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=self._handle_client, args=(client,), daemon=True
            ).start()

        self._sock.close()

    def _handle_client(self, client: socket.socket):
        try:
            client.settimeout(10)
            _ = client.recv(1024)  # 收到请求即响应
            data = pack_targets(self._ctx.db, self._ctx.user, self._ctx.host)
            client.sendall(len(data).to_bytes(4, "big"))
            client.sendall(data)
        except OSError:
            pass
        finally:
            try:
                client.close()
            except OSError:
                pass

    def stop(self):
        self._stop = True
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self.wait(3000)
