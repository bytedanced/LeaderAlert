"""摄像头采集线程。"""
import time

import cv2
from PySide6.QtCore import QThread, Signal

import config


class CameraThread(QThread):
    frame_ready = Signal(object)      # np.ndarray BGR 帧
    error_occurred = Signal(str)      # 打开/读取失败信息

    def __init__(self, index, fps=None, parent=None):
        super().__init__(parent)
        self._index = index
        self._fps = fps or config.CAMERA_FPS
        self._stop = False

    def run(self):
        # Windows 下 CAP_DSHOW 打开更快，失败再退回默认后端
        cap = cv2.VideoCapture(self._index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(self._index)
        if not cap.isOpened():
            self.error_occurred.emit(f"无法打开摄像头 {self._index}")
            return
        interval = 1.0 / self._fps
        while not self._stop:
            start = time.monotonic()
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.2)
                continue
            self.frame_ready.emit(frame)
            wait = interval - (time.monotonic() - start)
            if wait > 0:
                self.msleep(int(wait * 1000))
        cap.release()

    def stop(self):
        self._stop = True
        self.wait(5000)
