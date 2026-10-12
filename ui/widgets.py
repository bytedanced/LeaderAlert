"""通用 UI 资源：深色主题样式表、应用图标、无按钮数字输入框、拖拽文件列表。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QListWidget, QSpinBox

# 深色主题（紫 accent，卡片式布局）
DARK_QSS = """
* { font-family: 'Microsoft YaHei UI'; font-size: 13px; color: #e2e8f0; }
QMainWindow, QDialog { background: #0b1120; }

/* ---------- 侧边导航 ---------- */
QWidget#sideNav { background: #0f172a; border-right: 1px solid #1e293b; }
QLabel#navLogo { font-size: 16px; font-weight: bold; color: #a78bfa; padding: 18px 16px 4px; }
QLabel#navIdentity { color: #64748b; font-size: 11px; padding: 0 16px 14px; }
QPushButton[navItem="true"] {
    background: transparent; border: none; border-left: 3px solid transparent;
    border-radius: 0px; text-align: left; padding: 11px 16px; color: #94a3b8;
}
QPushButton[navItem="true"]:hover { background: #1e293b; color: #e2e8f0; }
QPushButton[navItem="true"]:checked {
    background: #1e1b33; color: #a78bfa; border-left: 3px solid #7c3aed; font-weight: bold;
}

/* ---------- 页面与卡片 ---------- */
QWidget#page { background: #0b1120; }
QLabel#pageTitle { font-size: 17px; font-weight: bold; padding: 2px 0; }
QLabel#pageHint { color: #64748b; }
QFrame#card {
    background: #111a2e; border: 1px solid #1e293b; border-radius: 12px;
}
QFrame#card:hover { border-color: #334155; }
QLabel#cardTitle { color: #94a3b8; font-size: 12px; }
QLabel#statNum { font-size: 26px; font-weight: bold; color: #e2e8f0; }
QLabel#statOk { color: #34d399; }
QLabel#statWarn { color: #fbbf24; }
QLabel#statErr { color: #f87171; }

/* ---------- 按钮 ---------- */
QPushButton {
    background: #1e293b; border: 1px solid #334155; border-radius: 8px;
    padding: 8px 18px; color: #e2e8f0;
}
QPushButton:hover { background: #334155; border-color: #475569; }
QPushButton:pressed { background: #475569; }
QPushButton:disabled { color: #64748b; background: #131c2e; }
QPushButton[primary="true"] {
    background: #7c3aed; border-color: #7c3aed; color: #ffffff; font-weight: bold;
}
QPushButton[primary="true"]:hover { background: #8b5cf6; border-color: #8b5cf6; }
QPushButton[primary="true"]:checked { background: #dc2626; border-color: #dc2626; }
QPushButton[primary="true"]:checked:hover { background: #ef4444; }
QPushButton[danger="true"] { border-color: #7f1d1d; color: #f87171; }
QPushButton[danger="true"]:hover { background: #7f1d1d; color: #ffffff; }
QPushButton[flat="true"] { background: transparent; border: none; color: #94a3b8; padding: 4px 10px; }
QPushButton[flat="true"]:hover { color: #e2e8f0; background: #1e293b; }

/* ---------- 输入 ---------- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    padding: 7px 10px; color: #e2e8f0; selection-background-color: #7c3aed;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #7c3aed; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #1e293b; border: 1px solid #334155; selection-background-color: #7c3aed; }
QCheckBox { spacing: 8px; }

/* ---------- 表格 ---------- */
QTableWidget { background: #111a2e; border: 1px solid #1e293b; border-radius: 10px; gridline-color: #1e293b; alternate-background-color: #16213a; }
QTableWidget::item { padding: 6px; border: none; }
QTableWidget::item:selected { background: #7c3aed; color: #ffffff; }
QHeaderView::section { background: #0f172a; border: none; border-bottom: 1px solid #1e293b; padding: 8px; color: #94a3b8; }

/* ---------- 列表 / 滚动 ---------- */
QListWidget { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; }
QListWidget::item { padding: 6px 8px; border-radius: 6px; }
QListWidget::item:selected { background: #7c3aed; color: #ffffff; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #334155; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #475569; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ---------- 其他 ---------- */
QGroupBox { border: 1px solid #1e293b; border-radius: 12px; margin-top: 16px; padding-top: 10px; background: #111a2e; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #94a3b8; }
QStatusBar { background: #0f172a; border-top: 1px solid #1e293b; color: #94a3b8; }
QStatusBar QLabel { color: #94a3b8; padding: 0 10px; }
QToolTip { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; }
QLabel#previewLabel { background: #050a16; border: 1px solid #1e293b; border-radius: 12px; color: #475569; }
QFrame#divider { background: #1e293b; max-height: 1px; }
"""


def make_app_icon() -> QIcon:
    """程序化生成应用图标（一只橙色眼睛，无外部图片依赖）。"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # 眼形底
    p.setPen(QPen(QColor("#f59e0b"), 5))
    p.setBrush(QColor("#1e293b"))
    p.drawEllipse(6, 14, 52, 36)
    # 瞳孔
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#f59e0b"))
    p.drawEllipse(26, 24, 12, 16)
    p.end()
    return QIcon(pm)


def make_spin(parent, minimum, maximum, value, decimals=0, step=1):
    """创建无上下箭头按钮的数字输入框。"""
    if decimals > 0:
        spin = QDoubleSpinBox(parent)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
    else:
        spin = QSpinBox(parent)
        spin.setSingleStep(int(step))
    spin.setRange(minimum, maximum)
    spin.setValue(value)
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setMinimumWidth(90)
    return spin


class DropFileList(QListWidget):
    """支持把系统文件拖入的列表控件，拖入后发出 files_dropped(路径列表)。"""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)

    def _accepts(self, event):
        return event.mimeData().hasUrls()

    def dragEnterEvent(self, event):
        if self._accepts(event):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._accepts(event):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not self._accepts(event):
            super().dropEvent(event)
            return
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        event.acceptProposedAction()
        if files:
            self.files_dropped.emit(files)
