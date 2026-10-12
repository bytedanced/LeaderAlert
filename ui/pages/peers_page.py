"""在线人员页：局域网内运行本软件的同事列表。"""
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from ui.pages.base import Page


class PeersPage(Page):
    def __init__(self, ctx, parent=None):
        super().__init__(
            ctx, "在线人员",
            f"同一局域网内正在运行本软件的同事（{ctx.heartbeat_interval()} 秒心跳，"
            f"{ctx.peer_timeout()} 秒无心跳判定离线）", parent)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["用户名", "主机名", "角色", "最后心跳"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
