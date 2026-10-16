"""报警动作页：检测到目标时的提醒方式（提示音 + 自动打开网页或文件）。"""
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from notify.action import run_action
from notify.notifier import play_sound, validate_sound_file
from ui.pages.base import Page


class ActionPage(Page):
    def __init__(self, ctx, parent=None):
        super().__init__(ctx, "报警动作", "检测到目标时的提醒方式：提示音与自动打开的网页或文件，保存后立即生效", parent)
        db = ctx.db

        # ---------- 提示音 ----------
        sound_group = QGroupBox("提示音（留空使用内置牛叫声）")
        sound_row = QHBoxLayout(sound_group)
        self._sound_edit = QLineEdit(db.get_str("sound_file") or "")
        self._sound_edit.setPlaceholderText("留空使用内置牛叫声（自定义仅支持 .wav）")
        btn_sound_browse = QPushButton("浏览…")
        btn_sound_test = QPushButton("试听")
        btn_sound_browse.clicked.connect(self._pick_sound)
        btn_sound_test.clicked.connect(self._test_sound)
        sound_row.addWidget(self._sound_edit, 1)
        sound_row.addWidget(btn_sound_browse)
        sound_row.addWidget(btn_sound_test)
        self.body().addWidget(sound_group)

        # ---------- 打开动作 ----------
        action_group = QGroupBox("打开动作（本机识别与同事报警均会触发，受报警冷却保护）")
        action_layout = QVBoxLayout(action_group)
        action_layout.setSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(8)
        self._action_edit = QLineEdit(db.get_str("alert_action") or "")
        self._action_edit.setPlaceholderText("网址（http/https）或本地文件/程序路径（如 D:\\work\\日报.docx），留空不执行")
        btn_browse = QPushButton("浏览…")
        btn_test = QPushButton("测试")
        btn_browse.clicked.connect(self._pick_action)
        btn_test.clicked.connect(lambda: run_action(self._action_edit.text()))
        row.addWidget(self._action_edit, 1)
        row.addWidget(btn_browse)
        row.addWidget(btn_test)
        action_layout.addLayout(row)

        hint = QLabel(
            "以 http:// 或 https:// 开头将用默认浏览器打开；"
            "其余按本地文件/程序路径交给系统打开（Word、PPT、Excel、exe、快捷方式均可）。"
        )
        hint.setStyleSheet("color: #94a3b8;")
        hint.setWordWrap(True)
        action_layout.addWidget(hint)
        self.body().addWidget(action_group)

        # ---------- 保存 ----------
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        btn_save = QPushButton("保存")
        btn_save.setProperty("primary", True)
        btn_save.setMinimumWidth(140)
        btn_save.clicked.connect(self._save)
        save_row.addWidget(btn_save)
        self.body().addLayout(save_row)
        self.body().addStretch(1)

    def _pick_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择提示音文件", "", "音频文件 (*.wav)")
        if path:
            self._sound_edit.setText(path)

    def _test_sound(self):
        err = play_sound(self._sound_edit.text().strip() or None)
        if err:
            QMessageBox.warning(self, "试听失败", err)

    def _pick_action(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件或程序", "", "所有文件 (*.*)")
        if path:
            self._action_edit.setText(path)

    def _save(self):
        sound_err = validate_sound_file(self._sound_edit.text().strip() or None)
        if sound_err:
            QMessageBox.warning(self, "提示音文件无效", sound_err)
            return
        db = self.ctx.db
        db.set_setting("sound_file", self._sound_edit.text().strip())
        db.set_setting("alert_action", self._action_edit.text().strip())
        self.ctx.apply_runtime_settings()  # 刷新通知器的提示音
        QMessageBox.information(self, "已保存", "报警动作已保存并生效")
