"""首次启动的身份设置对话框（仅用户名）。"""
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎使用领导来了预警")
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("首次使用，请输入你的名字")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        note = QLabel("同事的通知列表里会显示这个名字；\n识别到领导时也会标注报警来源。")
        note.setStyleSheet("color: #94a3b8;")
        note.setWordWrap(True)

        self._edit = QLineEdit()
        self._edit.setPlaceholderText("例如：张三")
        self._edit.setMaxLength(20)
        self._edit.textChanged.connect(self._on_text_changed)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("进入")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("退出")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(note)
        layout.addWidget(self._edit)
        layout.addWidget(buttons)

    def user_name(self) -> str:
        return self._edit.text().strip()

    def _on_text_changed(self, text):
        ok_btn = self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setEnabled(bool(text.strip()))
