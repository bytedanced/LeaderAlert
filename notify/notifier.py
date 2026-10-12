"""Windows 系统通知与提示音。"""
import os
from datetime import datetime

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QSystemTrayIcon


def play_sound(sound_file=None):
    """播放提示音：自定义 wav 文件优先，否则系统蜂鸣。"""
    try:
        import winsound

        if sound_file and os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass  # 音频失败不影响通知


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
