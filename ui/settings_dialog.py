"""设置对话框：识别参数、提示音、领导照片管理、开机自启。"""
import os
import shutil
import sys
import uuid
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import config
from app.application import set_autostart
from detector.recognizer import RecognizerError
from notify.notifier import play_sound
from storage import paths
from ui.widgets import make_spin


class SettingsDialog(QDialog):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.db = ctx.db
        self.setWindowTitle("设置")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(self._build_detect_group())
        layout.addWidget(self._build_sound_group())
        layout.addWidget(self._build_leader_group())
        layout.addWidget(self._build_misc_group())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load()

    # ---------- 构建界面 ----------
    def _build_detect_group(self):
        group = QGroupBox("识别参数")
        form = QFormLayout(group)
        form.setSpacing(8)

        self._camera = QComboBox()
        for i in range(5):
            self._camera.addItem(f"摄像头 {i}", i)

        self._threshold = make_spin(self, 0.30, 0.60, config.SIM_THRESHOLD, decimals=2, step=0.01)
        self._confirm_window = make_spin(self, 2, 10, config.CONFIRM_WINDOW)
        self._confirm_hits = make_spin(self, 1, 9, config.CONFIRM_HITS)
        self._cooldown = make_spin(self, 1, 60, config.COOLDOWN_SECONDS // 60)

        self._param_note = QLabel("阈值越高越严格；命中帧数需 ≤ 窗口帧数")
        self._param_note.setStyleSheet("color: #94a3b8;")

        form.addRow("摄像头", self._camera)
        form.addRow("相似度阈值", self._threshold)
        form.addRow("确认窗口（帧）", self._confirm_window)
        form.addRow("命中帧数", self._confirm_hits)
        form.addRow("报警冷却（分钟）", self._cooldown)
        form.addRow(self._param_note)
        return group

    def _build_sound_group(self):
        group = QGroupBox("报警提示音")
        row = QHBoxLayout(group)
        self._sound_edit = QLineEdit()
        self._sound_edit.setPlaceholderText("留空使用系统提示音（wav 文件）")
        btn_browse = QPushButton("浏览...")
        btn_test = QPushButton("测试")
        btn_browse.clicked.connect(self._pick_sound)
        btn_test.clicked.connect(lambda: play_sound(self._sound_edit.text().strip() or None))
        row.addWidget(self._sound_edit, 1)
        row.addWidget(btn_browse)
        row.addWidget(btn_test)
        return group

    def _build_leader_group(self):
        group = QGroupBox("领导照片（识别端本地特征库，不联网不同步）")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self._leader_list = QListWidget()
        self._leader_list.setMaximumHeight(140)
        layout.addWidget(self._leader_list)

        row = QHBoxLayout()
        btn_add = QPushButton("添加照片")
        btn_del = QPushButton("删除选中")
        btn_add.clicked.connect(self._add_photos)
        btn_del.clicked.connect(self._remove_selected)
        self._leader_count = QLabel()
        self._leader_count.setStyleSheet("color: #94a3b8;")
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        row.addStretch(1)
        row.addWidget(self._leader_count)
        layout.addLayout(row)
        return group

    def _build_misc_group(self):
        group = QGroupBox("其他")
        layout = QVBoxLayout(group)
        self._autostart = QCheckBox("开机自动启动")
        if not getattr(sys, "frozen", False):
            self._autostart.setEnabled(False)
            self._autostart.setToolTip("开发模式下不可用，打包后生效")
        layout.addWidget(self._autostart)
        return group

    # ---------- 数据 ----------
    def _load(self):
        self._camera.setCurrentIndex(self.db.get_int("camera_index", 0))
        self._threshold.setValue(self.db.get_float("sim_threshold", config.SIM_THRESHOLD))
        self._confirm_window.setValue(self.db.get_int("confirm_window", config.CONFIRM_WINDOW))
        self._confirm_hits.setValue(self.db.get_int("confirm_hits", config.CONFIRM_HITS))
        self._cooldown.setValue(self.db.get_int("cooldown_seconds", config.COOLDOWN_SECONDS) // 60)
        self._sound_edit.setText(self.db.get_str("sound_file") or "")
        self._autostart.setChecked(self.db.get_str("autostart") == "1")
        self._refresh_leader_list()

    def _save_and_close(self):
        hits = self._confirm_hits.value()
        window = self._confirm_window.value()
        if hits > window:
            QMessageBox.warning(self, "参数有误", "命中帧数不能大于确认窗口帧数")
            return
        self.db.set_setting("camera_index", self._camera.currentData())
        self.db.set_setting("sim_threshold", self._threshold.value())
        self.db.set_setting("confirm_window", window)
        self.db.set_setting("confirm_hits", hits)
        self.db.set_setting("cooldown_seconds", self._cooldown.value() * 60)
        self.db.set_setting("sound_file", self._sound_edit.text().strip())
        enabled = self._autostart.isChecked()
        self.db.set_setting("autostart", "1" if enabled else "0")
        set_autostart(enabled)
        self.accept()

    # ---------- 领导照片管理 ----------
    def _refresh_leader_list(self):
        self._leader_list.clear()
        for _id, photo, created in self.db.list_leader_faces():
            created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d %H:%M")
            name = os.path.basename(photo) if photo else "-"
            self._leader_list.addItem(f"{created_str}  {name}")
        self._leader_count.setText(f"共 {self.db.count_leader_faces()} 条特征")

    def _add_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择领导照片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        if not files:
            return
        try:
            recognizer = self.ctx.get_recognizer()
        except RecognizerError as e:
            QMessageBox.critical(self, "识别引擎不可用", str(e))
            return
        ok, fail = 0, []
        for path in files:
            try:
                emb = recognizer.enroll(path)
                dest = os.path.join(paths.leader_photos_dir(), f"{uuid.uuid4().hex}{os.path.splitext(path)[1]}")
                shutil.copy(path, dest)
                self.db.add_leader_face(emb, dest)
                ok += 1
            except (RecognizerError, OSError) as e:
                fail.append(f"{os.path.basename(path)}：{e}")
        recognizer.reload_leader_embeddings()
        self._refresh_leader_list()
        if fail:
            QMessageBox.warning(self, "部分照片录入失败", "\n".join(fail))

    def _remove_selected(self):
        rows = self.db.list_leader_faces()
        index = self._leader_list.currentRow()
        if index < 0 or index >= len(rows):
            return
        face_id = rows[index][0]
        self.db.delete_leader_face(face_id)
        try:
            recognizer = self.ctx.get_recognizer()
            recognizer.reload_leader_embeddings()
        except RecognizerError:
            pass  # 特征库仍会随下次初始化重载
        self._refresh_leader_list()
