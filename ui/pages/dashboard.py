"""仪表盘页：识别控制、状态统计卡、摄像头实时预览。"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton

from detector.recognizer import RecognizerError
from ui.pages.base import Card, Page, StatCard


class DashboardPage(Page):
    def __init__(self, ctx, parent=None):
        super().__init__(ctx, "仪表盘", "识别运行状态与实时画面", parent)

        # ---------- 状态统计卡 ----------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self._stat_detector = StatCard("识别状态")
        self._stat_online = StatCard("在线人数")
        self._stat_targets = StatCard("监控目标")
        self._stat_cooldown = StatCard("报警冷却")
        for card in (self._stat_detector, self._stat_online, self._stat_targets, self._stat_cooldown):
            stats_row.addWidget(card, 1)
        self.body().addLayout(stats_row)

        # ---------- 预览卡 ----------
        preview_card = Card()
        head = QHBoxLayout()
        title = QLabel("摄像头预览")
        title.setObjectName("cardTitle")
        head.addWidget(title)
        head.addStretch(1)
        self._engine_label = QLabel("")
        self._engine_label.setObjectName("pageHint")
        head.addWidget(self._engine_label)
        self._btn_toggle = QPushButton("启动识别")
        self._btn_toggle.setProperty("primary", True)
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.setMinimumWidth(140)
        self._btn_toggle.clicked.connect(self._on_toggle)
        head.addWidget(self._btn_toggle)
        preview_card.body().addLayout(head)

        self._preview = QLabel("识别未启动 — 点击右上角「启动识别」开始监控")
        self._preview.setObjectName("previewLabel")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumHeight(380)
        preview_card.body().addWidget(self._preview)
        self.body().addWidget(preview_card, 1)

        # ---------- 信号 ----------
        ctx.detector.state_changed.connect(self._on_state)
        ctx.detector.preview_frame.connect(self._on_preview)
        ctx.detector.error_occurred.connect(self._on_error)
        ctx.peers_changed.connect(self.refresh_stats)
        ctx.alerts_changed.connect(self.refresh_stats)

        self.refresh_stats()

    # ---------- 对外 ----------
    def refresh_stats(self):
        db = self.ctx.db
        running = self.ctx.detector.running
        self._stat_detector.set_value("运行中" if running else "已停止",
                                      f"摄像头 {db.get_int('camera_index', 0)}",
                                      "ok" if running else None)
        self._stat_online.set_value(len(self.ctx.peers) + 1, "含自己")
        self._stat_targets.set_value(db.count_targets(), f"照片 {db.count_leader_faces()} 张")
        left = self.ctx.cooldown_left()
        if left > 0:
            self._stat_cooldown.set_value(f"{left}s", "冷却中，期间不重复报警", "warn")
        else:
            self._stat_cooldown.set_value("就绪", "可随时触发报警", "ok")

    # ---------- 识别控制 ----------
    def _on_toggle(self, checked):
        if checked:
            self._start()
        else:
            self.ctx.detector.stop()

    def _start(self):
        db = self.ctx.db
        if db.count_leader_faces() == 0:
            QMessageBox.warning(self, "无法启动", "请先在「牛管理」中新建目标并录入照片")
            self._btn_toggle.setChecked(False)
            return
        try:
            recognizer = self.ctx.get_recognizer()  # 首次会加载模型，稍慢
        except RecognizerError as e:
            QMessageBox.critical(self, "识别引擎不可用", str(e))
            self._btn_toggle.setChecked(False)
            return
        self.ctx.detector.start(db.get_int("camera_index", 0), recognizer)

    def restart_if_camera_changed(self, old_camera):
        """设置页改了摄像头后，运行中则重启识别。"""
        if self.ctx.detector.running and self.ctx.db.get_int("camera_index", 0) != old_camera:
            self.ctx.detector.stop()
            self._start()

    # ---------- 信号处理 ----------
    def _on_state(self, running):
        self._btn_toggle.setChecked(running)
        self._btn_toggle.setText("停止识别" if running else "启动识别")
        if running:
            try:
                self._engine_label.setText(f"引擎：{self.ctx.get_recognizer().engine_name}")
            except RecognizerError:
                self._engine_label.setText("")
        else:
            self._preview.setText("识别未启动 — 点击右上角「启动识别」开始监控")
            self._preview.setPixmap(QPixmap())
        self.refresh_stats()

    def _on_error(self, message):
        self._btn_toggle.setChecked(False)
        QMessageBox.critical(self, "识别出错", message)

    def _on_preview(self, frame, _boxes):
        h, w = frame.shape[0], frame.shape[1]
        image = QImage(frame.data, w, h, w * 3, QImage.Format.Format_BGR888).copy()
        pix = QPixmap.fromImage(image).scaled(
            self._preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview.setPixmap(pix)
