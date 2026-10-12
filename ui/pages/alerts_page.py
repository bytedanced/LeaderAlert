"""报警历史页：时间线卡片流，含抓拍缩略图，点击查看大图。"""
import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from storage import paths
from ui.pages.base import Page


class SnapshotViewer(QDialog):
    """报警抓拍大图查看。"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(os.path.basename(image_path))
        layout = QVBoxLayout(self)
        label = QLabel()
        pix = QPixmap(image_path)
        if not pix.isNull():
            label.setPixmap(pix.scaled(
                800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(label)


class AlertCard(QFrame):
    """单条报警的时间线卡片。"""

    def __init__(self, user, host, ts, target, snapshot, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # 缩略图（无抓拍则显示占位）
        thumb = QLabel()
        thumb.setFixedSize(96, 72)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("background: #0f172a; border-radius: 8px; color: #475569;")
        self._snapshot_path = None
        if snapshot:
            full = os.path.join(paths.snapshots_dir(), snapshot)
            if os.path.exists(full):
                pm = QPixmap(full)
                if not pm.isNull():
                    thumb.setPixmap(pm.scaled(96, 72, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation))
                    self._snapshot_path = full
        if self._snapshot_path is None:
            thumb.setText("无抓拍")
        layout.addWidget(thumb)

        # 文案区
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        who = QLabel(f"🐮 {target}" if target else "牛来了！")
        who.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
        source = QLabel(f"识别来源：{user}（{host}）")
        source.setStyleSheet("color: #94a3b8;")
        time_label = QLabel(datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"))
        time_label.setStyleSheet("color: #64748b; font-size: 12px;")
        text_col.addWidget(who)
        text_col.addWidget(source)
        text_col.addWidget(time_label)
        layout.addLayout(text_col, 1)

        if self._snapshot_path:
            btn = QPushButton("查看大图")
            btn.setProperty("flat", True)
            btn.clicked.connect(self._open)
            layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def _open(self):
        SnapshotViewer(self._snapshot_path, self).exec()


class AlertsPage(Page):
    def __init__(self, ctx, parent=None):
        super().__init__(ctx, "报警历史", "识别到目标的全部记录，本机识别含现场抓拍", parent)

        top = QHBoxLayout()
        top.addStretch(1)
        btn_clear = QPushButton("清空记录")
        btn_clear.setProperty("danger", True)
        btn_clear.clicked.connect(self._clear)
        top.addWidget(btn_clear)
        self.body().addLayout(top)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 6, 0)
        self._list_layout.setSpacing(10)
        self._list_layout.addStretch(1)
        self._scroll.setWidget(self._container)
        self.body().addWidget(self._scroll, 1)

        ctx.alerts_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        # 清空旧卡片（保留末尾 stretch）
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rows = self.ctx.db.recent_alerts()
        if not rows:
            empty = QLabel("暂无报警记录")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #475569; padding: 40px;")
            self._list_layout.insertWidget(0, empty)
            return
        for i, (_id, user, host, ts, target, snapshot) in enumerate(rows):
            self._list_layout.insertWidget(i, AlertCard(user, host, ts, target, snapshot))

    def _clear(self):
        if QMessageBox.question(self, "确认", "确定清空全部报警记录吗？") == QMessageBox.StandardButton.Yes:
            self.ctx.db.clear_alerts()
            self.refresh()
