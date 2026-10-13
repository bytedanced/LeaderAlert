"""TCP 数据同步客户端：从在线同事拉取牛管理数据（单 JSON 字节）。"""
import socket

from storage.sync_pack import import_targets  # noqa: F401  re-export 供 UI 使用


class SyncError(Exception):
    """同步失败。"""


def fetch_targets(ip: str, port: int, timeout: int = 10) -> bytes:
    """从指定 peer 拉取数据，返回 JSON 字节（内存中，不落盘）。失败抛 SyncError。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
        except socket.timeout:
            raise SyncError(f"连接 {ip}:{port} 超时")
        except OSError as e:
            raise SyncError(f"连接 {ip}:{port} 失败：{e}")

        sock.sendall(b"SYNC")
        header = _recv_exact(sock, 4)
        if header is None:
            raise SyncError("对方未响应数据长度")
        size = int.from_bytes(header, "big")
        if size <= 0 or size > 100 * 1024 * 1024:  # 限制 100MB
            raise SyncError(f"数据长度异常：{size}")
        data = _recv_exact(sock, size)
        if data is None:
            raise SyncError(f"数据接收不完整（{size} 字节）")
        return data
    finally:
        sock.close()


def _recv_exact(sock: socket.socket, n: int):
    """精确读取 n 字节，超时/断开返回 None。"""
    buf = bytearray()
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except socket.timeout:
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)
