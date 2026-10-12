"""通用 UI 资源：深色主题样式表、应用图标、无按钮数字输入框。"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QSpinBox

# 深色主题（紫色 accent）
DARK_QSS = """
* { font-family: 'Microsoft YaHei UI'; font-size: 12px; color: #e2e8f0; }
QMainWindow, QDialog { background: #0f172a; }
QToolBar { background: #0b1220; border: none; border-bottom: 1px solid #1e293b; spacing: 8px; padding: 6px; }
QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 6px 16px; color: #e2e8f0; }
QPushButton:hover { background: #334155; border-color: #475569; }
QPushButton:pressed { background: #475569; }
QPushButton:checked { background: #7c3aed; border-color: #7c3aed; color: #ffffff; }
QPushButton:checked:hover { background: #8b5cf6; }
QPushButton:disabled { color: #64748b; background: #131c2e; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #1e293b; border: 1px solid #334155; border-radius: 6px;
    padding: 4px 8px; color: #e2e8f0; selection-background-color: #7c3aed;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background: #1e293b; border: 1px solid #334155; selection-background-color: #7c3aed; }
QTableWidget { background: #111c33; border: 1px solid #1e293b; gridline-color: #1e293b; alternate-background-color: #16213a; }
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background: #7c3aed; color: #ffffff; }
QHeaderView::section { background: #1e293b; border: none; border-right: 1px solid #0f172a; padding: 6px; color: #94a3b8; }
QTabWidget::pane { border: 1px solid #1e293b; border-radius: 6px; top: -1px; }
QTabBar::tab { background: #1e293b; padding: 8px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; color: #94a3b8; }
QTabBar::tab:selected { background: #7c3aed; color: #ffffff; }
QGroupBox { border: 1px solid #1e293b; border-radius: 8px; margin-top: 14px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #94a3b8; }
QStatusBar { background: #0b1220; border-top: 1px solid #1e293b; color: #94a3b8; }
QStatusBar QLabel { color: #94a3b8; padding: 0 8px; }
QToolTip { background: #1e293b; color: #e2e8f0; border: 1px solid #334155; }
QListWidget { background: #111c33; border: 1px solid #1e293b; border-radius: 6px; }
QListWidget::item { padding: 6px 8px; }
QListWidget::item:selected { background: #7c3aed; color: #ffffff; }
QLabel#previewLabel { background: #0b1220; border: 1px solid #1e293b; border-radius: 6px; }
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
