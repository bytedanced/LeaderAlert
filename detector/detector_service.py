"""识别编排服务：摄像头采集线程 + 识别处理线程。

处理流程：CameraThread 采集（节流到 CAMERA_FPS）→ 帧队列（满则丢弃）→
ProcessingThread 识别 → 发出预览帧信号 / 报警确认信号。
"""
import queue

import cv2
from PySide6.QtCore import QObject, QThread, Signal

from detector.camera import CameraThread


class ProcessingThread(QThread):
    preview_frame = Signal(object, object)  # 已画框的帧, 人脸框列表
    alert_confirmed = Signal(object)         # 确认报警时的原始帧（用于抓拍）

    def __init__(self, recognizer, frame_queue, parent=None):
        super().__init__(parent)
        self._recognizer = recognizer
        self._queue = frame_queue
        self._stop = False

    def run(self):
        while not self._stop:
            try:
                frame = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                result = self._recognizer.process(frame)
            except Exception:
                continue  # 单帧失败不影响后续
            drawn = frame.copy()
            # 命中领导画红框，普通人脸画绿框
            color = (68, 44, 232) if result.hit else (185, 231, 122)  # BGR：红 / 绿
            for x1, y1, x2, y2 in result.boxes:
                cv2.rectangle(drawn, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            self.preview_frame.emit(drawn, result.boxes)
            if result.confirmed:
                self.alert_confirmed.emit(frame)

    def stop(self):
        self._stop = True
        self.wait(5000)


class DetectorService(QObject):
    """识别服务门面：start/stop 摄像头与识别线程。"""

    preview_frame = Signal(object, object)
    alert_confirmed = Signal(object)
    error_occurred = Signal(str)
    state_changed = Signal(bool)  # 运行状态

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self._camera = None
        self._processing = None
        self._queue = None

    def start(self, camera_index, recognizer):
        if self.running:
            self.stop()
        self._queue = queue.Queue(maxsize=1)  # 处理不过来时丢帧，保持实时性
        self._processing = ProcessingThread(recognizer, self._queue)
        self._processing.preview_frame.connect(self.preview_frame)
        self._processing.alert_confirmed.connect(self.alert_confirmed)
        self._camera = CameraThread(camera_index)
        self._camera.frame_ready.connect(self._enqueue_frame)
        self._camera.error_occurred.connect(self._on_camera_error)
        self._processing.start()
        self._camera.start()
        self.running = True
        self.state_changed.emit(True)

    def stop(self):
        if self._camera is not None:
            self._camera.stop()
            self._camera = None
        if self._processing is not None:
            self._processing.stop()
            self._processing = None
        self._queue = None
        if self.running:
            self.running = False
            self.state_changed.emit(False)

    # ---------- 内部 ----------
    def _enqueue_frame(self, frame):
        if self._queue is None:
            return
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            pass  # 丢弃积压帧

    def _on_camera_error(self, message):
        self.stop()
        self.error_occurred.emit(message)
