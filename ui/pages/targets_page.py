"""牛管理页：目标人物卡片网格 + 单目标照片管理弹窗（拖拽/预览/删除）。"""
import os
import shutil
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from detector.recognizer import RecognizerError
from storage import paths
from ui.pages.base import Page


class DropScrollArea(QScrollArea):
    """支持拖入文件的滚动区域（照片墙容器）。"""

    def __init__(self, on_dropped, parent=None):
        super().__init__(parent)
        self._on_dropped = on_dropped
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            super().dropEvent(event)
            return
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        event.acceptProposedAction()
        if files:
            self._on_dropped(files)


class PhotoThumb(QFrame):
    """照片墙单格：缩略图 + 删除按钮；点击看大图。"""

    def __init__(self, dialog, photo, face_id, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 178)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; }"
            "QFrame:hover { border-color: #7c3aed; }")
        self._dialog = dialog
        self._photo = photo
        self._face_id = face_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        thumb = QLabel()
        thumb.setFixedSize(134, 120)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("border: none; color: #475569;")
        pm = QPixmap(photo) if photo and os.path.exists(photo) else QPixmap()
        if pm.isNull():
            thumb.setText("无法加载")
        else:
            thumb.setPixmap(pm.scaled(134, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(thumb)

        btn_del = QPushButton("删除")
        btn_del.setProperty("danger", True)
        btn_del.setStyleSheet("padding: 4px 0px; font-size: 12px;")
        btn_del.clicked.connect(self._delete)
        layout.addWidget(btn_del)

    def mousePressEvent(self, event):
        child = self.childAt(event.position().toPoint())
        if not isinstance(child, QPushButton) and self._photo and os.path.exists(self._photo):
            os.startfile(self._photo)
        super().mousePressEvent(event)

    def _delete(self):
        self._dialog.delete_photo(self._face_id, self._photo)


class PhotosDialog(QDialog):
    """单个目标的照片管理：照片墙 + 拖拽录入。"""

    def __init__(self, ctx, target_id, target_name, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.target_id = target_id
        self.setWindowTitle(f"管理照片 — {target_name}")
        self.resize(560, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel("拖拽图片到下方区域直接录入；点击缩略图查看原图")
        hint.setStyleSheet("color: #64748b;")
        layout.addWidget(hint)

        self._scroll = DropScrollArea(self._enroll)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(10)
        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll, 1)

        row = QHBoxLayout()
        btn_add = QPushButton("添加照片")
        btn_add.clicked.connect(self._add_photos)
        row.addWidget(btn_add)
        row.addStretch(1)
        self._count = QLabel()
        self._count.setStyleSheet("color: #94a3b8;")
        row.addWidget(self._count)
        btn_close = QPushButton("完成")
        btn_close.setProperty("primary", True)
        btn_close.clicked.connect(self.accept)
        row.addWidget(btn_close)
        layout.addLayout(row)

        self._refresh()

    # ---------- 数据 ----------
    def _refresh(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        rows = self.ctx.db.list_leader_faces(self.target_id)
        if not rows:
            empty = QLabel("暂无照片，把图片拖进来或点「添加照片」")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #475569; padding: 60px;")
            self._grid.addWidget(empty, 0, 0)
        else:
            cols = max(1, (self._scroll.viewport().width() - 10) // 160)
            for i, (face_id, photo, _created) in enumerate(rows):
                self._grid.addWidget(PhotoThumb(self, photo, face_id), i // cols, i % cols)
        self._count.setText(f"共 {len(rows)} 条特征")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()  # 宽度变化后按新列数重排

    # ---------- 录入 / 删除 ----------
    def _add_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)")
        if files:
            self._enroll(files)

    def _enroll(self, files):
        try:
            recognizer = self.ctx.get_recognizer()
        except RecognizerError as e:
            QMessageBox.critical(self, "识别引擎不可用", str(e))
            return
        fail = []
        for path in files:
            try:
                emb = recognizer.enroll(path)
                dest = os.path.join(paths.leader_photos_dir(),
                                    f"{uuid.uuid4().hex}{os.path.splitext(path)[1]}")
                shutil.copy(path, dest)
                self.ctx.db.add_leader_face(emb, dest, self.target_id)
            except (RecognizerError, OSError) as e:
                fail.append(f"{os.path.basename(path)}：{e}")
        recognizer.reload_leader_embeddings()
        self._refresh()
        if fail:
            QMessageBox.warning(self, "部分照片录入失败", "\n".join(fail))

    def delete_photo(self, face_id, photo):
        self.ctx.db.delete_leader_face(face_id)
        if photo:
            try:
                os.remove(photo)
            except OSError:
                pass
        try:
            self.ctx.get_recognizer().reload_leader_embeddings()
        except RecognizerError:
            pass
        self._refresh()


class TargetCard(QFrame):
    """人物卡片：头像缩略图 + 姓名 + 照片数；点击卡片打开照片管理。"""

    def __init__(self, page, target_id, name, photos, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedSize(200, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._page = page
        self._target_id = target_id
        self._name = name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)

        thumb = QLabel()
        thumb.setFixedSize(172, 120)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("background: #0f172a; border-radius: 8px; color: #475569;")
        first_photo = photos[0] if photos else None
        pm = QPixmap(first_photo) if first_photo and os.path.exists(first_photo) else QPixmap()
        if pm.isNull():
            thumb.setText("暂无照片\n点击录入")
        else:
            thumb.setPixmap(pm.scaled(172, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(thumb)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(name_label)

        count_label = QLabel(f"{len(photos)} 张照片")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(count_label)

        row = QHBoxLayout()
        row.setSpacing(6)
        btn_rename = QPushButton("改名")
        btn_del = QPushButton("删除")
        btn_del.setProperty("danger", True)
        for b in (btn_rename, btn_del):
            b.setStyleSheet("padding: 5px 0px; font-size: 12px;")
        btn_rename.clicked.connect(self._rename)
        btn_del.clicked.connect(self._delete)
        row.addWidget(btn_rename, 1)
        row.addWidget(btn_del, 1)
        layout.addLayout(row)

    def mousePressEvent(self, event):
        # 点在按钮上不触发卡片点击
        child = self.childAt(event.position().toPoint())
        if not isinstance(child, QPushButton):
            self._manage_photos()
        super().mousePressEvent(event)

    def _manage_photos(self):
        PhotosDialog(self._page.ctx, self._target_id, self._name, self).exec()
        self._page.refresh()

    def _rename(self):
        name, ok = QInputDialog.getText(self, "重命名目标", "目标姓名：", text=self._name)
        name = name.strip()
        if ok and name and name != self._name:
            self._page.ctx.db.rename_target(self._target_id, name)
            self._page.refresh()

    def _delete(self):
        answer = QMessageBox.question(
            self, "删除目标",
            f"确定删除目标「{self._name}」及其全部照片特征吗？\n（磁盘上的照片文件会一并清理）")
        if answer != QMessageBox.StandardButton.Yes:
            return
        for photo in self._page.ctx.db.delete_target(self._target_id):
            try:
                os.remove(photo)
            except OSError:
                pass
        try:
            self._page.ctx.get_recognizer().reload_leader_embeddings()
        except RecognizerError:
            pass
        self._page.refresh()


class NewTargetCard(QFrame):
    """「+ 新建目标」虚线卡片。"""

    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QFrame { background: transparent; border: 2px dashed #334155; border-radius: 12px; }"
            "QFrame:hover { border-color: #7c3aed; }")
        self._page = page
        layout = QVBoxLayout(self)
        label = QLabel("＋")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 36px; color: #7c3aed; border: none;")
        text = QLabel("新建目标")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet("color: #94a3b8; border: none;")
        layout.addStretch(1)
        layout.addWidget(label)
        layout.addWidget(text)
        layout.addStretch(1)

    def mousePressEvent(self, _event):
        name, ok = QInputDialog.getText(self, "新建目标", "目标姓名：")
        name = name.strip()
        if not ok or not name:
            return
        if any(t[1] == name for t in self._page.ctx.db.list_targets()):
            QMessageBox.warning(self, "新建失败", f"目标「{name}」已存在")
            return
        self._page.ctx.db.add_target(name)
        self._page.refresh()


class TargetsPage(Page):
    """牛管理：目标人物卡片网格。"""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, "牛管理", "为每个需要识别的人维护照片特征库（仅本机保存，不联网不同步）", parent)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(0, 0, 6, 0)
        self._grid.setSpacing(14)
        self._scroll.setWidget(self._container)
        self.body().addWidget(self._scroll, 1)

        self.refresh()

    def refresh(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        db = self.ctx.db
        targets = db.list_targets()
        # 每个目标的照片路径列表
        photos_by_target = {}
        for tid, name, _c in targets:
            photos_by_target[tid] = [p for _id, p, _c2 in db.list_leader_faces(tid) if p]

        cols = max(1, (self._scroll.viewport().width() - 6) // 214)
        index = 0
        for tid, name, _c in targets:
            card = TargetCard(self, tid, name, photos_by_target.get(tid, []))
            self._grid.addWidget(card, index // cols, index % cols)
            index += 1
        self._grid.addWidget(NewTargetCard(self), index // cols, index % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 宽度变化后按新列数重排
        self.refresh()
