"""主窗口：在线人员、报警历史、摄像头预览、识别控制。"""
import os
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import config
from detector.recognizer import RecognizerError
from storage import paths
from ui.settings_dialog import SettingsDialog


class SnapshotViewer(QDialog):
    """报警抓拍大图查看。"""

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(os.path.basename(image_path))
        layout = QVBoxLayout(self)
        label = QLabel()
        pix = QPixmap(image_path)
        if not pix.isNull():
            label.setPixmap(pix.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(label)


class MainWindow(QMainWindow):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle(f"{config.APP_NAME} - 领导来了预警")
        self.resize(920, 640)
        self._tray_tipped = False

        # ---------- 顶部工具栏 ----------
        self._btn_toggle = QPushButton("启动识别")
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.clicked.connect(self._on_toggle_detection)
        btn_settings = QPushButton("设置")
        btn_settings.clicked.connect(self._open_settings)

        self._identity_label = QLabel(f"身份：{ctx.user}@{ctx.host}")
        self._identity_label.setStyleSheet("color: #94a3b8;")
        self._online_label = QLabel("在线：1 人（含自己）")
        self._online_label.setStyleSheet("color: #94a3b8;")

        toolbar = QWidget()
        toolbar.setLayout(QHBoxLayout())
        toolbar.layout().setContentsMargins(10, 4, 10, 4)
        toolbar.layout().addWidget(self._identity_label)
        toolbar.layout().addStretch(1)
        toolbar.layout().addWidget(self._online_label)
        toolbar.layout().addWidget(self._btn_toggle)
        toolbar.layout().addWidget(btn_settings)

        # ---------- 中心区（Tab） ----------
        self._tabs = QTabWidget()

        # 在线人员
        self._online_table = QTableWidget(0, 4)
        self._online_table.setHorizontalHeaderLabels(["用户名", "主机名", "角色", "最后心跳"])
        self._online_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._online_table.setAlternatingRowColors(True)
        self._online_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._online_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tabs.addTab(self._online_table, "在线人员")

        # 报警历史
        alerts_tab = QWidget()
        alerts_layout = QVBoxLayout(alerts_tab)
        alerts_layout.setContentsMargins(0, 8, 0, 0)
        self._alerts_table = QTableWidget(0, 3)
        self._alerts_table.setHorizontalHeaderLabels(["时间", "识别来源", "抓拍"])
        self._alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._alerts_table.setAlternatingRowColors(True)
        self._alerts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._alerts_table.cellDoubleClicked.connect(self._on_alert_double_clicked)
        btn_clear = QPushButton("清空记录")
        btn_clear.clicked.connect(self._clear_alerts)
        btn_clear.setFixedWidth(100)
        row = QHBoxLayout()
        hint = QLabel("双击带「查看」的记录可打开抓拍大图；远程报警无本地抓拍")
        hint.setStyleSheet("color: #94a3b8;")
        row.addWidget(hint)
        row.addStretch(1)
        row.addWidget(btn_clear)
        alerts_layout.addLayout(row)
        alerts_layout.addWidget(self._alerts_table)
        self._tabs.addTab(alerts_tab, "报警历史")

        # 摄像头预览
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        preview_layout.setContentsMargins(0, 8, 0, 0)
        self._preview_label = QLabel("识别未启动")
        self._preview_label.setObjectName("previewLabel")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(640, 360)
        preview_layout.addWidget(self._preview_label)
        self._tabs.addTab(preview_tab, "摄像头预览")

        # ---------- 状态栏 ----------
        status = QStatusBar()
        self._status_detector = QLabel("识别：未启动")
        self._status_udp = QLabel("UDP：等待心跳...")
        self._status_leader = QLabel(f"领导照片：{self.ctx.db.count_leader_faces()} 条")
        self._status_cooldown = QLabel("")
        status.addWidget(self._status_detector)
        status.addWidget(self._status_udp)
        status.addWidget(self._status_leader)
        status.addPermanentWidget(self._status_cooldown)

        central = QWidget()
        central.setLayout(QVBoxLayout())
        central.layout().setContentsMargins(0, 0, 0, 0)
        central.layout().addWidget(toolbar)
        central.layout().addWidget(self._tabs)
        self.setCentralWidget(central)
        self.setStatusBar(status)

        # ---------- 信号连接 ----------
        self.ctx.peers_changed.connect(self._refresh_online)
        self.ctx.alerts_changed.connect(self._refresh_alerts)
        self.ctx.detector.state_changed.connect(self._on_detector_state)
        self.ctx.detector.preview_frame.connect(self._on_preview)
        self.ctx.detector.alert_confirmed.connect(self.ctx.submit_local_alert)
        self.ctx.detector.error_occurred.connect(self._on_detector_error)

        # ---------- 定时刷新 ----------
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start()

        self._setup_tray()
        self._refresh_online()
        self._refresh_alerts()

    # ---------- 托盘 ----------
    def _setup_tray(self):
        menu = QMenu()
        act_show = menu.addAction("显示主窗口")
        act_quit = menu.addAction("退出")
        act_show.triggered.connect(self.show_and_raise)
        act_quit.triggered.connect(self._quit)
        self.ctx.tray.setContextMenu(menu)
        self.ctx.tray.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_and_raise()

    def show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---------- 识别控制 ----------
    def _on_toggle_detection(self, checked):
        if checked:
            self._start_detection()
        else:
            self.ctx.detector.stop()

    def _start_detection(self):
        db = self.ctx.db
        if db.count_leader_faces() == 0:
            QMessageBox.warning(self, "无法启动", "请先在「设置」中录入领导照片")
            self._btn_toggle.setChecked(False)
            return
        camera_index = db.get_int("camera_index", 0)
        try:
            recognizer = self.ctx.get_recognizer()  # 首次会加载模型，稍慢
        except RecognizerError as e:
            QMessageBox.critical(self, "识别引擎不可用", str(e))
            self._btn_toggle.setChecked(False)
            return
        self.ctx.detector.start(camera_index, recognizer)

    def _on_detector_state(self, running):
        self._btn_toggle.setChecked(running)
        self._btn_toggle.setText("停止识别" if running else "启动识别")
        self._status_detector.setText(f"识别：运行中（摄像头 {self.ctx.db.get_int('camera_index', 0)}）" if running else "识别：未启动")

    def _on_detector_error(self, message):
        self._btn_toggle.setChecked(False)
        QMessageBox.critical(self, "识别出错", message)

    def _on_preview(self, frame, _boxes):
        h, w = frame.shape[0], frame.shape[1]
        image = QImage(frame.data, w, h, w * 3, QImage.Format.Format_BGR888).copy()
        pix = QPixmap.fromImage(image).scaled(
            self._preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(pix)

    # ---------- 表格刷新 ----------
    def _refresh_online(self):
        peers = sorted(self.ctx.peers.values(), key=lambda p: p.user)
        self._online_table.setRowCount(len(peers))
        for i, p in enumerate(peers):
            role = "识别端" if p.role == "detector" else "接收端"
            last = datetime.fromtimestamp(p.last_seen).strftime("%H:%M:%S")
            for j, text in enumerate((p.user, p.host, role, last)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._online_table.setItem(i, j, item)
        self._online_label.setText(f"在线：{len(peers) + 1} 人（含自己）")

    def _refresh_alerts(self):
        rows = self.ctx.db.recent_alerts()
        self._alerts_table.setRowCount(len(rows))
        for i, (_id, user, host, ts, snapshot) in enumerate(rows):
            time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            source = f"{user}（{host}）"
            snap_text = "查看" if snapshot else "—"
            for j, text in enumerate((time_str, source, snap_text)):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._alerts_table.setItem(i, j, item)

    def _clear_alerts(self):
        if QMessageBox.question(self, "确认", "确定清空全部报警记录吗？") == QMessageBox.StandardButton.Yes:
            self.ctx.db.clear_alerts()
            self._refresh_alerts()

    def _on_alert_double_clicked(self, row, _col):
        rows = self.ctx.db.recent_alerts()
        if row >= len(rows):
            return
        snapshot = rows[row][4]
        if not snapshot:
            return
        path = os.path.join(paths.snapshots_dir(), snapshot)
        if os.path.exists(path):
            SnapshotViewer(path, self).exec()
        else:
            QMessageBox.information(self, "提示", "抓拍文件不存在或已被清理")

    # ---------- 设置 ----------
    def _open_settings(self):
        was_running = self.ctx.detector.running
        old_camera = self.ctx.db.get_int("camera_index", 0)
        dialog = SettingsDialog(self.ctx, self)
        if dialog.exec():
            self.ctx.apply_runtime_settings()
            self._status_leader.setText(f"领导照片：{self.ctx.db.count_leader_faces()} 条")
            new_camera = self.ctx.db.get_int("camera_index", 0)
            if was_running and new_camera != old_camera:
                self.ctx.detector.stop()
                self._start_detection()  # 换摄像头后重启识别

    # ---------- 定时任务 ----------
    def _on_timer(self):
        self.ctx.prune_peers()
        left = self.ctx.cooldown_left()
        if left > 0:
            self._status_cooldown.setText(f"报警冷却中：剩 {left}s")
        else:
            self._status_cooldown.setText("")
        if self.ctx.udp_ok and self._status_udp.text() != "UDP：正常":
            self._status_udp.setText("UDP：正常")

    # ---------- 关闭行为 ----------
    def closeEvent(self, event):
        """关闭窗口 → 最小化到托盘，程序继续运行。"""
        event.ignore()
        self.hide()
        if not self._tray_tipped:
            self._tray_tipped = True
            self.ctx.tray.showMessage(
                "程序在后台运行",
                "主窗口已最小化到托盘，双击托盘图标可重新打开；退出请通过托盘菜单。",
            )

    def _quit(self):
        self.ctx.shutdown()
        from PySide6.QtWidgets import QApplication

        QApplication.quit()
