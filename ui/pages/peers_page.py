"""在线人员页：局域网内运行本软件的同事列表，支持从同事导入牛管理数据。"""
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from detector.recognizer import RecognizerError
from network.sync_client import SyncError, fetch_targets
from storage.sync_pack import import_targets, list_conflicts
from ui.pages.base import Page


class _FetchWorker(QThread):
    """后台拉取同事数据，避免网络操作冻结 GUI。"""

    done = Signal(bytes)
    failed = Signal(str)

    def __init__(self, ip, port, parent=None):
        super().__init__(parent)
        self._ip = ip
        self._port = port

    def run(self):
        try:
            self.done.emit(fetch_targets(self._ip, self._port))
        except SyncError as e:
            self.failed.emit(str(e))


class PeersPage(Page):
    def __init__(self, ctx, parent=None):
        super().__init__(
            ctx, "在线人员",
            f"同一局域网内正在运行本软件的同事（{ctx.heartbeat_interval()} 秒心跳，"
            f"{ctx.peer_timeout()} 秒无心跳判定离线）", parent)

        self._busy = False       # 有导入任务进行中
        self._worker = None      # 保持引用防止被 GC
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["用户名", "主机名", "角色", "最后心跳", "操作"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self.body().addWidget(self._table, 1)

        ctx.peers_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        peers = sorted(self.ctx.peers.values(), key=lambda p: p.user)
        self._table.setRowCount(len(peers))
        for i, p in enumerate(peers):
            role = "识别端" if p.role == "detector" else "接收端"
            last = datetime.fromtimestamp(p.last_seen).strftime("%H:%M:%S")
            for j, text in enumerate((p.user, p.host, role, last)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(i, j, item)
            btn = QPushButton("同步中…" if self._busy else "导入牛数据")
            btn.setProperty("flat", True)
            btn.setEnabled(not self._busy and bool(p.ip and p.sync_port))
            btn.setToolTip(f"从 {p.user}@{p.host} 导入目标库" if p.ip else "等待对方心跳同步端口")
            btn.clicked.connect(lambda _c=False, peer=p: self._import_from_peer(peer))
            self._table.setCellWidget(i, 4, btn)

    # ---------- 导入 ----------
    def _import_from_peer(self, peer):
        if self._busy:
            return
        if not peer.ip or not peer.sync_port:
            QMessageBox.warning(self, "无法导入", "对方尚未同步端口信息，请稍后再试")
            return
        self._busy = True
        self.refresh()
        self._worker = _FetchWorker(peer.ip, peer.sync_port, self)
        self._worker.done.connect(lambda data: self._on_fetched(peer, data))
        self._worker.failed.connect(self._on_fetch_failed)
        self._worker.start()

    def _on_fetched(self, peer, data: bytes):
        self._busy = False
        try:
            conflicts = list_conflicts(data, self.ctx.db)
        except (ValueError, OSError) as e:
            self._on_fetch_failed(str(e))
            return

        if conflicts:
            action = self._ask_conflict(conflicts)
            if action is None:
                self.refresh()
                return  # 用户取消
            conflict_map = {name: action for name in conflicts}
        else:
            conflict_map = {}

        try:
            stats = import_targets(data, self.ctx.db, conflict_map)
        except (ValueError, OSError) as e:
            QMessageBox.critical(self, "导入失败", str(e))
            self.refresh()
            return

        try:
            self.ctx.get_recognizer().reload_leader_embeddings()
        except RecognizerError:
            pass

        msg = [f"已从 {peer.user}@{peer.host} 导入完成："]
        if stats["imported"]:
            msg.append(f"导入 {stats['imported']} 个目标（{stats['imported_faces']} 张照片特征）")
        if stats["overwritten"]:
            msg.append(f"覆盖 {stats['overwritten']} 个同名目标")
        if stats["renamed"]:
            msg.append(f"重命名 {stats['renamed']} 个目标")
        if stats["skipped"]:
            msg.append(f"跳过 {stats['skipped']} 个同名目标")
        if not stats["imported"]:
            msg.append("对方没有可导入的数据")
        QMessageBox.information(self, "导入完成", "\n".join(msg))
        self.refresh()

    def _on_fetch_failed(self, message: str):
        self._busy = False
        QMessageBox.critical(self, "导入失败", message)
        self.refresh()

    def _ask_conflict(self, conflict_names: list):
        """一次性询问同名目标的处理策略，返回 'skip'/'overwrite'/'rename'；取消返回 None。"""
        box = QMessageBox(self)
        box.setWindowTitle("同名目标")
        names = "、".join(f"「{n}」" for n in conflict_names)
        box.setText(f"以下目标在本地已存在：{names}\n\n如何处理这些同名目标？")
        btn_skip = box.addButton("跳过", QMessageBox.ButtonRole.RejectRole)
        btn_overwrite = box.addButton("覆盖本地", QMessageBox.ButtonRole.DestructiveRole)
        btn_rename = box.addButton("重命名导入", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("取消导入", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_skip:
            return "skip"
        if clicked is btn_overwrite:
            return "overwrite"
        if clicked is btn_rename:
            return "rename"
        return None
