"""应用上下文：全局状态、网络/识别/通知模块装配、报警统一处理。"""
import os
import socket
import sys
import time
from datetime import datetime

import cv2
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QSystemTrayIcon

import config
from detector.detector_service import DetectorService
from detector.recognizer import Recognizer, RecognizerError
from network.broadcaster import Broadcaster
from network.listener import ListenerThread
from network.sync_server import SyncServerThread
from notify.action import run_action
from notify.notifier import Notifier
from storage import paths
from ui.widgets import make_app_icon


class PeerInfo:
    """在线同事信息。"""

    def __init__(self, user, host, role, last_seen, ip="", sync_port=0):
        self.user = user
        self.host = host
        self.role = role
        self.last_seen = last_seen
        self.ip = ip
        self.sync_port = sync_port


def set_autostart(enabled: bool) -> bool:
    """写入/删除注册表开机自启项。仅打包后生效，返回是否成功。"""
    if not getattr(sys, "frozen", False):
        return False
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, config.APP_NAME, 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try:
                    winreg.DeleteValue(key, config.APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


class AppContext(QObject):
    """全局装配中心：持有身份、在线表、冷却状态，串联各模块信号。"""

    peers_changed = Signal()   # 在线列表变化
    alerts_changed = Signal()  # 报警记录变化

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        identity = db.get_identity()
        self.user = identity[0]
        self.host = socket.gethostname()
        self.peers = {}           # key: "user@host" -> PeerInfo
        self.udp_ok = True
        self._last_alert_ts = 0.0
        self._alert_seq = 0
        self._recognizer = None
        self._recognizer_error = None

        # 托盘图标
        self.tray = QSystemTrayIcon(make_app_icon(), self)
        self.tray.setToolTip(f"牛来了预警 v{config.APP_VERSION}：{self.user}@{self.host}")
        self.tray.show()

        # 通知器
        self.notifier = Notifier(self.tray, self)
        self.notifier.set_sound_file(db.get_str("sound_file"))

        # 识别服务
        self.detector = DetectorService(self)

        # 网络
        self.broadcaster = None
        self.listener = None
        self.sync_server = None
        self._start_network()

    # ---------- 网络参数 ----------
    def udp_port(self) -> int:
        return self.db.get_int("udp_port", config.UDP_PORT)

    def sync_port(self) -> int:
        """TCP 数据同步端口（默认 UDP 端口 + 1）。"""
        return self.db.get_int("sync_port", self.udp_port() + 1)

    def broadcast_addrs(self):
        """广播地址列表（设置中逗号分隔多个）。"""
        raw = self.db.get_str("broadcast_addrs", config.BROADCAST_ADDR) or config.BROADCAST_ADDR
        addrs = [a.strip() for a in raw.split(",") if a.strip()]
        return addrs or [config.BROADCAST_ADDR]

    def heartbeat_interval(self) -> int:
        return max(1, self.db.get_int("heartbeat_interval", config.HEARTBEAT_INTERVAL))

    def peer_timeout(self) -> int:
        return max(5, self.db.get_int("peer_timeout", config.PEER_TIMEOUT))

    def _start_network(self):
        self.broadcaster = Broadcaster(self, self)
        self.listener = ListenerThread(self.udp_port(), self)
        self.listener.heartbeat_received.connect(self._on_heartbeat)
        self.listener.alert_received.connect(self._on_remote_alert)
        self.listener.bind_failed.connect(self._on_bind_failed)
        self.broadcaster.start()
        self.listener.start()
        self.sync_server = SyncServerThread(self, self.sync_port(), self)
        self.sync_server.start()

    def restart_network(self):
        """网络参数变更后重启收发模块。"""
        if self.listener is not None:
            self.listener.stop()
        if self.broadcaster is not None:
            self.broadcaster.stop()
        if self.sync_server is not None:
            self.sync_server.stop()
        self.peers.clear()
        self.peers_changed.emit()
        self.udp_ok = True
        self._start_network()

    # ---------- 状态 ----------
    def role(self) -> str:
        """心跳中的角色声明：detector / receiver。"""
        return "detector" if self.detector.running else "receiver"

    def cooldown_left(self) -> int:
        """距冷却结束剩余秒数。"""
        cooldown = self.db.get_int("cooldown_seconds", config.COOLDOWN_SECONDS)
        left = cooldown - (time.time() - self._last_alert_ts)
        return max(0, int(left))

    # ---------- 在线列表 ----------
    def _on_heartbeat(self, msg, addr):
        key = f"{msg.user}@{msg.host}"
        if key == f"{self.user}@{self.host}":
            return  # 忽略自己
        self.peers[key] = PeerInfo(
            msg.user, msg.host, msg.role, time.time(),
            ip=addr[0], sync_port=msg.sync_port,
        )
        self.peers_changed.emit()

    def prune_peers(self):
        """清理超时未心跳的同事。"""
        now = time.time()
        timeout = self.peer_timeout()
        stale = [k for k, v in self.peers.items() if now - v.last_seen > timeout]
        if stale:
            for k in stale:
                self.peers.pop(k)
            self.peers_changed.emit()

    # ---------- 报警处理 ----------
    def _on_remote_alert(self, msg):
        self.handle_alert(msg.user, msg.host, msg.ts, frame=None, target=msg.target)

    def submit_local_alert(self, frame, target=""):
        """本机识别确认后的报警：广播 + 本机通知。target 为命中的目标名。"""
        self.broadcaster.send_alert(target)
        self.handle_alert(self.user, self.host, time.time(), frame=frame, target=target)

    def handle_alert(self, user, host, ts, frame=None, target=None):
        """报警统一入口：全局冷却去重 → 抓拍 → 落库 → 通知。"""
        cooldown = self.db.get_int("cooldown_seconds", config.COOLDOWN_SECONDS)
        if time.time() - self._last_alert_ts < cooldown:
            return  # 冷却期内静默（多端同时识别天然去重）
        self._last_alert_ts = time.time()

        snapshot = None
        if frame is not None:
            self._alert_seq += 1
            snapshot = "alert_{}_{}.jpg".format(
                datetime.now().strftime("%Y%m%d_%H%M%S"), self._alert_seq
            )
            cv2.imwrite(os.path.join(paths.snapshots_dir(), snapshot), frame)
        self.db.add_alert(user, host, ts, snapshot, target)
        self.notifier.show_alert(user, host, ts, target)
        run_action(self.db.get_str("alert_action"))
        self.alerts_changed.emit()

    # ---------- 识别器 ----------
    def get_recognizer(self) -> Recognizer:
        """懒加载识别器（首次初始化含模型加载，可能耗时数秒）。"""
        if self._recognizer is None and self._recognizer_error is None:
            try:
                self._recognizer = Recognizer(self.db, paths.model_root())
            except Exception as e:
                self._recognizer_error = str(e)
        if self._recognizer_error is not None:
            raise RecognizerError(self._recognizer_error)
        return self._recognizer

    def apply_runtime_settings(self):
        """设置变更后刷新运行时参数。"""
        if self._recognizer is not None:
            self._recognizer.set_params(
                self.db.get_float("sim_threshold", config.SIM_THRESHOLD),
                self.db.get_int("confirm_window", config.CONFIRM_WINDOW),
                self.db.get_int("confirm_hits", config.CONFIRM_HITS),
            )
            self._recognizer.reload_leader_embeddings()
        self.notifier.set_sound_file(self.db.get_str("sound_file"))

    # ---------- 网络 ----------
    def _on_bind_failed(self, message):
        self.udp_ok = False
        self.tray.showMessage(
            "网络提示",
            f"UDP 端口 {self.udp_port()} 绑定失败，无法接收广播：{message}",
            QSystemTrayIcon.MessageIcon.Warning,
            5000,
        )

    def shutdown(self):
        """退出前清理。"""
        self.detector.stop()
        if self.sync_server is not None:
            self.sync_server.stop()
        if self.listener is not None:
            self.listener.stop()
        if self.broadcaster is not None:
            self.broadcaster.stop()
        self.tray.hide()
