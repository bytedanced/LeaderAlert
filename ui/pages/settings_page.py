"""设置页（内嵌）：识别参数、网络、提示音、开机自启。"""
import ipaddress
import os
import sys

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from notify.notifier import play_sound
from ui.pages.base import Page
from ui.widgets import make_spin


class SettingsPage(Page):
    def __init__(self, ctx, on_saved=None, parent=None):
        super().__init__(ctx, "设置", "识别参数与通知方式，保存后立即生效", parent)
        self._on_saved = on_saved
        db = ctx.db

        # ---------- 识别参数 ----------
        detect_group = QGroupBox("识别参数")
        form = QFormLayout(detect_group)
        form.setSpacing(12)
        self._camera = QComboBox()
        for i in range(4):
            self._camera.addItem(f"摄像头 {i}", i)
        self._camera.setCurrentIndex(db.get_int("camera_index", 0))
        self._threshold = make_spin(self, 20, 90, round(db.get_float("sim_threshold", config.SIM_THRESHOLD) * 100), decimals=2, step=1)
        self._confirm_window = make_spin(self, 3, 30, db.get_int("confirm_window", config.CONFIRM_WINDOW))
        self._confirm_hits = make_spin(self, 1, 30, db.get_int("confirm_hits", config.CONFIRM_HITS))
        self._cooldown = make_spin(self, 10, 1000, db.get_int("cooldown_seconds", config.COOLDOWN_SECONDS))
        form.addRow("摄像头", self._camera)
        form.addRow("相似度阈值（0.2~0.9，越大越严格）", self._threshold)
        form.addRow("确认窗口（帧）", self._confirm_window)
        form.addRow("窗口内命中帧数", self._confirm_hits)
        form.addRow("报警冷却（秒）", self._cooldown)
        self.body().addWidget(detect_group)

        # ---------- 网络 ----------
        net_group = QGroupBox("网络（保存后立即重连生效）")
        net_layout = QVBoxLayout(net_group)
        net_layout.setSpacing(12)
        net_form = QFormLayout()
        net_form.setSpacing(12)
        self._udp_port = make_spin(self, 1024, 65535, db.get_int("udp_port", config.UDP_PORT))
        self._heartbeat = make_spin(self, 1, 60, db.get_int("heartbeat_interval", config.HEARTBEAT_INTERVAL))
        self._peer_timeout = make_spin(self, 5, 600, db.get_int("peer_timeout", config.PEER_TIMEOUT))
        net_form.addRow("UDP 端口（全员需一致）", self._udp_port)
        net_form.addRow("心跳间隔（秒）", self._heartbeat)
        net_form.addRow("离线判定（秒）", self._peer_timeout)
        net_layout.addLayout(net_form)

        addr_label = QLabel("广播地址（心跳/报警会同时发往每个地址）")
        addr_label.setStyleSheet("color: #94a3b8;")
        net_layout.addWidget(addr_label)
        addr_row = QHBoxLayout()
        addr_row.setSpacing(8)
        self._addr_list = QListWidget()
        self._addr_list.setMaximumHeight(110)
        raw = db.get_str("broadcast_addrs", config.BROADCAST_ADDR) or config.BROADCAST_ADDR
        for a in [x.strip() for x in raw.split(",") if x.strip()]:
            self._addr_list.addItem(a)
        addr_row.addWidget(self._addr_list, 1)
        addr_btns = QVBoxLayout()
        addr_btns.setSpacing(6)
        self._addr_input = QLineEdit()
        self._addr_input.setPlaceholderText("如 172.18.72.255")
        btn_addr_add = QPushButton("添加")
        btn_addr_del = QPushButton("删除选中")
        btn_addr_del.setProperty("danger", True)
        btn_addr_add.clicked.connect(self._add_addr)
        btn_addr_del.clicked.connect(self._del_addr)
        self._addr_input.returnPressed.connect(self._add_addr)
        addr_btns.addWidget(self._addr_input)
        addr_btns.addWidget(btn_addr_add)
        addr_btns.addWidget(btn_addr_del)
        addr_btns.addStretch(1)
        addr_row.addLayout(addr_btns)
        net_layout.addLayout(addr_row)
        self.body().addWidget(net_group)

        # ---------- 提示音 ----------
        sound_group = QGroupBox("提示音")
        sound_row = QHBoxLayout(sound_group)
        self._sound_edit = QLineEdit(db.get_str("sound_file") or "")
        self._sound_edit.setPlaceholderText("留空使用系统默认提示音（仅支持 .wav）")
        btn_browse = QPushButton("浏览…")
        btn_test = QPushButton("试听")
        btn_browse.clicked.connect(self._pick_sound)
        btn_test.clicked.connect(lambda: play_sound(self._sound_edit.text().strip() or None))
        sound_row.addWidget(self._sound_edit, 1)
        sound_row.addWidget(btn_browse)
        sound_row.addWidget(btn_test)
        self.body().addWidget(sound_group)

        # ---------- 其他 ----------
        misc_group = QGroupBox("其他")
        misc_layout = QVBoxLayout(misc_group)
        self._autostart = QCheckBox("开机自动启动")
        self._autostart.setChecked(db.get_str("autostart") == "1")
        if not getattr(sys, "frozen", False):
            self._autostart.setEnabled(False)
            self._autostart.setToolTip("开发模式下不可用，打包后生效")
        misc_layout.addWidget(self._autostart)
        self.body().addWidget(misc_group)

        # ---------- 保存 ----------
        row = QHBoxLayout()
        row.addStretch(1)
        btn_save = QPushButton("保存设置")
        btn_save.setProperty("primary", True)
        btn_save.setMinimumWidth(140)
        btn_save.clicked.connect(self._save)
        row.addWidget(btn_save)
        self.body().addLayout(row)
        self.body().addStretch(1)

    def _pick_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择提示音文件", "", "音频文件 (*.wav)")
        if path:
            self._sound_edit.setText(path)

    # ---------- 广播地址列表 ----------
    def _add_addr(self):
        addr = self._addr_input.text().strip()
        if not addr:
            return
        try:
            ipaddress.IPv4Address(addr)
        except ipaddress.AddressValueError:
            QMessageBox.warning(self, "地址无效", f"「{addr}」不是合法的 IPv4 地址")
            return
        for i in range(self._addr_list.count()):
            if self._addr_list.item(i).text() == addr:
                QMessageBox.warning(self, "添加失败", f"地址「{addr}」已在列表中")
                return
        self._addr_list.addItem(addr)
        self._addr_input.clear()
        self._addr_input.setFocus()

    def _del_addr(self):
        row = self._addr_list.currentRow()
        if row >= 0:
            self._addr_list.takeItem(row)

    def _addr_values(self):
        return [self._addr_list.item(i).text() for i in range(self._addr_list.count())]

    def _save(self):
        hits = self._confirm_hits.value()
        window = self._confirm_window.value()
        if hits > window:
            QMessageBox.warning(self, "参数有误", "命中帧数不能大于确认窗口帧数")
            return
        addrs = ", ".join(self._addr_values())
        if not addrs:
            QMessageBox.warning(self, "参数有误", "广播地址列表不能为空，请至少添加一个")
            return
        old_camera = self.ctx.db.get_int("camera_index", 0)
        old_net = (
            self.ctx.db.get_int("udp_port", config.UDP_PORT),
            self.ctx.db.get_str("broadcast_addrs", config.BROADCAST_ADDR),
            self.ctx.db.get_int("heartbeat_interval", config.HEARTBEAT_INTERVAL),
        )
        db = self.ctx.db
        db.set_setting("camera_index", self._camera.currentData())
        db.set_setting("sim_threshold", self._threshold.value() / 100)
        db.set_setting("confirm_window", window)
        db.set_setting("confirm_hits", hits)
        db.set_setting("cooldown_seconds", self._cooldown.value())
        db.set_setting("sound_file", self._sound_edit.text().strip())
        db.set_setting("udp_port", self._udp_port.value())
        db.set_setting("broadcast_addrs", addrs)
        db.set_setting("heartbeat_interval", self._heartbeat.value())
        db.set_setting("peer_timeout", self._peer_timeout.value())
        enabled = self._autostart.isChecked()
        db.set_setting("autostart", "1" if enabled else "0")
        set_autostart(enabled)
        self.ctx.apply_runtime_settings()
        new_net = (self._udp_port.value(), addrs, self._heartbeat.value())
        if new_net != old_net:
            self.ctx.restart_network()
        if self._on_saved:
            self._on_saved(old_camera)
        QMessageBox.information(self, "已保存", "设置已保存并生效")
