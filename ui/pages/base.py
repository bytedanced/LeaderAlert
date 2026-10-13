"""页面基类与公共组件：页面标题、统计卡、卡片容器。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget


class Page(QWidget):
    """内嵌页面基类：统一标题区 + 提示语，内容区放入滚动容器以免撑住窗口最小尺寸。"""

    def __init__(self, ctx, title, hint="", parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self.ctx = ctx
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(24, 20, 24, 16)
        self._root.setSpacing(14)

        head = QVBoxLayout()
        head.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("pageTitle")
        head.addWidget(t)
        if hint:
            h = QLabel(hint)
            h.setObjectName("pageHint")
            head.addWidget(h)
        self._root.addLayout(head)

        line = QFrame()
        line.setObjectName("divider")
        self._root.addWidget(line)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._body = QWidget()
        self._body.setObjectName("pageBody")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(14)
        self._scroll.setWidget(self._body)
        self._root.addWidget(self._scroll, 1)

    def body(self) -> QVBoxLayout:
        return self._body_layout


class Card(QFrame):
    """圆角卡片容器。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 16)
        self._layout.setSpacing(10)

    def body(self) -> QVBoxLayout:
        return self._layout


class StatCard(Card):
    """统计卡：标题 + 大数字 + 副文案。"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(150)
        label = QLabel(title)
        label.setObjectName("cardTitle")
        self._num = QLabel("—")
        self._num.setObjectName("statNum")
        self._sub = QLabel("")
        self._sub.setObjectName("pageHint")
        self.body().addWidget(label)
        self.body().addWidget(self._num)
        self.body().addWidget(self._sub)

    def set_value(self, num, sub="", level=None):
        """level: None / 'ok' / 'warn' / 'err'，控制数字颜色。"""
        self._num.setText(str(num))
        self._num.setStyleSheet({
            "ok": "color: #34d399;", "warn": "color: #fbbf24;",
            "err": "color: #f87171;", None: "",
        }.get(level, ""))
        self._sub.setText(sub)
