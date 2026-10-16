"""Windows 系统通知与提示音。"""
import os
import sys
import wave
from datetime import datetime

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QSystemTrayIcon


def default_sound_file():
    """内置默认提示音（牛叫声）：开发态取 assets/sounds/，打包态取 _MEIPASS/sounds/。"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base:
            path = os.path.join(base, "sounds", "cowmoo.wav")
            if os.path.exists(path):
                return path
        return None
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "sounds", "cowmoo.wav",
    )
    return path if os.path.exists(path) else None


def validate_sound_file(sound_file):
    """校验声音文件，返回错误信息（None 表示可用）。

    winsound 只能播标准 PCM WAV；文件不存在或非 PCM 编码（如 mp3 改后缀、
    float32/ADPCM 编码）都无法播放，需提前给出明确原因。
    """
    if not sound_file:
        return None
    if not os.path.exists(sound_file):
        return f"声音文件不存在：{sound_file}"
    if not sound_file.lower().endswith(".wav"):
        return f"仅支持 .wav 文件：{sound_file}"
    try:
        with wave.open(sound_file, "rb"):
            return None
    except wave.Error:
        return "不是有效的 PCM WAV 文件（可能是 mp3 改后缀或特殊编码），请换用标准 wav"


def play_sound(sound_file=None):
    """播放提示音：自定义 wav 优先，否则内置牛叫声，最后系统蜂鸣。返回错误信息（None 表示成功）。"""
    try:
        import winsound

        file = sound_file or default_sound_file()
        if file:
            err = validate_sound_file(file)
            if err:
                return err
            winsound.PlaySound(file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        return None
    except Exception as e:
        return f"播放失败：{e}"


class Notifier(QObject):
    """通过托盘图标发送 Windows 系统通知。"""

    def __init__(self, tray: QSystemTrayIcon, parent=None):
        super().__init__(parent)
        self._tray = tray
        self._sound_file = None

    def set_sound_file(self, path):
        self._sound_file = path

    def sound_file(self):
        return self._sound_file

    def show_alert(self, user, host, ts, target=None):
        """弹出「牛来了」通知，标注是谁来了和识别来源。"""
        t = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        title = f"牛来了：{target}" if target else "牛来了！"
        body = f"【{target}】由 {user}（{host}）的摄像头识别到 {t}" if target else \
            f"由 {user}（{host}）的摄像头识别到 {t}"
        self._tray.showMessage(
            title,
            body,
            QSystemTrayIcon.MessageIcon.Warning,
            5000,
        )
        play_sound(self._sound_file)
