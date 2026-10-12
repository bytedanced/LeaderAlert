"""人脸识别封装。

双引擎设计：
- InsightFaceEngine：insightface 包（buffalo_s 模型），精度高（带关键点对齐），需要 pip 装上 insightface
- OnnxEngine：OpenCV 级联检测 + onnxruntime 直接跑 buffalo_s 的识别模型，无 insightface 时的兜底

对外统一接口：detect_and_embed(frame) -> [(bbox, embedding), ...]
"""
import os
import threading
from collections import deque

import cv2
import numpy as np

import config
from storage.database import Database


class RecognizerError(Exception):
    """识别引擎初始化/执行失败。"""


class FrameResult:
    """单帧识别结果。boxes 为人脸框 (x1, y1, x2, y2) 列表，hit 为本帧是否命中目标，
    confirmed 为滑窗确认，target 为确认时命中的目标名（未确认为 None）。"""

    def __init__(self, boxes, hit, confirmed, target=None):
        self.boxes = boxes
        self.hit = hit
        self.confirmed = confirmed
        self.target = target


class InsightFaceEngine:
    """insightface 引擎：检测 + 关键点对齐 + 特征提取。"""

    def __init__(self, model_root, det_size):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as e:
            raise RecognizerError(f"insightface 未安装：{e}") from e
        try:
            self._app = FaceAnalysis(
                name="buffalo_s",
                root=model_root,
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"],
            )
            self._app.prepare(ctx_id=-1, det_size=det_size)
        except Exception as e:
            raise RecognizerError(f"insightface 初始化失败：{e}") from e

    def detect_and_embed(self, frame):
        faces = self._app.get(frame)
        out = []
        for f in faces:
            if f.normed_embedding is None:
                continue
            box = tuple(map(float, f.bbox))
            out.append((box, np.asarray(f.normed_embedding, dtype=np.float32)))
        return out

    def name(self):
        return "insightface"


class OnnxEngine:
    """兜底引擎：Haar 级联检测 + onnxruntime 特征提取（无关键点对齐，精度略低）。"""

    def __init__(self, model_root, det_size):
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if self._cascade.empty():
            raise RecognizerError("OpenCV 人脸级联模型加载失败")
        model_path = self._find_recognition_model(model_root)
        if not model_path:
            raise RecognizerError(
                "未找到 buffalo_s 识别模型（w600k_mbf.onnx）。"
                "请先联网运行一次让 insightface 自动下载，或手动放置模型到 assets/models/buffalo_s/"
            )
        import onnxruntime as ort

        self._sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self._input_name = self._sess.get_inputs()[0].name

    @staticmethod
    def _find_recognition_model(model_root):
        """在 buffalo_s 目录中找识别模型（ArcFace 系特征模型以 w 开头，如 w600k_mbf.onnx）。"""
        for base in (
            os.path.join(model_root, "models", "buffalo_s"),
            os.path.join(os.path.expanduser("~/.insightface"), "models", "buffalo_s"),
        ):
            if os.path.isdir(base):
                for fname in os.listdir(base):
                    if fname.endswith(".onnx") and fname.startswith("w"):
                        return os.path.join(base, fname)
        return None

    def _embed(self, face_img):
        face = cv2.resize(face_img, (112, 112))
        blob = cv2.dnn.blobFromImage(
            face, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True
        )
        emb = self._sess.run(None, {self._input_name: blob})[0][0].astype(np.float32)
        return emb / (np.linalg.norm(emb) + 1e-9)

    def detect_and_embed(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self._cascade.detectMultiScale(
            gray, scaleFactor=1.15, minNeighbors=5, minSize=(60, 60)
        )
        out = []
        for x, y, w, h in rects:
            emb = self._embed(frame[y:y + h, x:x + w])
            out.append(((float(x), float(y), float(x + w), float(y + h)), emb))
        return out

    def name(self):
        return "onnx-fallback"


class Recognizer:
    """识别器门面：参数管理、领导特征库比对、多帧滑窗确认。"""

    def __init__(self, db: Database, model_root: str):
        self._db = db
        self._lock = threading.Lock()
        self._threshold = db.get_float("sim_threshold", config.SIM_THRESHOLD)
        self._confirm_window = db.get_int("confirm_window", config.CONFIRM_WINDOW)
        self._confirm_hits = db.get_int("confirm_hits", config.CONFIRM_HITS)

        # 优先 insightface，失败则退回 onnx 兜底
        primary_error = None
        self._engine = None
        try:
            self._engine = InsightFaceEngine(model_root, config.DET_SIZE)
        except Exception as e:
            primary_error = e
        if self._engine is None:
            try:
                self._engine = OnnxEngine(model_root, config.DET_SIZE)
            except Exception as e2:
                raise RecognizerError(
                    f"识别引擎初始化失败。\n主引擎(insightface)：{primary_error}\n兜底引擎(onnx)：{e2}"
                ) from e2

        self.engine_name = self._engine.name()
        self._window = deque(maxlen=self._confirm_window)
        self._embeddings = []  # [(特征向量, 目标名), ...]
        self._last_hit_target = None
        self.reload_leader_embeddings()

    # ---------- 参数与特征库 ----------
    def set_params(self, threshold: float, confirm_window: int, confirm_hits: int) -> None:
        with self._lock:
            self._threshold = threshold
            self._confirm_window = confirm_window
            self._confirm_hits = confirm_hits
            self._window = deque(maxlen=confirm_window)

    def reload_leader_embeddings(self) -> None:
        with self._lock:
            self._embeddings = self._db.load_leader_embeddings()

    def leader_count(self) -> int:
        return len(self._embeddings)

    # ---------- 识别 ----------
    def process(self, frame) -> FrameResult:
        """处理一帧：检测 + 比对 + 滑窗确认。"""
        with self._lock:
            faces = self._engine.detect_and_embed(frame)
            boxes = [f[0] for f in faces]
            hit, hit_target = False, None
            for _box, emb in faces:
                name, score = self._best_match(emb)
                if score >= self._threshold:
                    hit, hit_target = True, name
                    break
            if hit:
                self._last_hit_target = hit_target
            self._window.append(hit)
            confirmed = sum(self._window) >= self._confirm_hits
            if confirmed:
                self._window.clear()  # 确认后清空窗口，冷却逻辑由上层负责
                return FrameResult(boxes, hit, True, self._last_hit_target)
            return FrameResult(boxes, hit, False)

    def _best_match(self, emb):
        """返回特征库中最高相似度的 (目标名, 相似度)；库为空返回 (None, 0)。"""
        if not self._embeddings:
            return None, 0.0
        best_name, best = None, 0.0
        for ref, name in self._embeddings:
            score = float(np.dot(emb, ref))
            if score > best:
                best, best_name = score, name
        return best_name, best

    # ---------- 录入 ----------
    def enroll(self, image_path: str):
        """从照片提取领导特征：取画面中最大的人脸。"""
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RecognizerError(f"无法读取图片：{image_path}")
        faces = self._engine.detect_and_embed(img)
        if not faces:
            raise RecognizerError("照片中未检测到人脸，请换一张正面清晰的照片")
        box, emb = max(faces, key=lambda f: (f[0][2] - f[0][0]) * (f[0][3] - f[0][1]))
        return emb
