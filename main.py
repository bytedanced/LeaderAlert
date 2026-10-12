"""领导来了预警系统入口。"""
import argparse
import sys

from PySide6.QtWidgets import QApplication

from app.application import AppContext
from storage import paths
from storage.database import Database
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from ui.widgets import DARK_QSS, make_app_icon


def main():
    parser = argparse.ArgumentParser(description="领导来了预警系统")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="数据目录覆盖（用于同机多实例测试），默认为项目/exe 同级 data/",
    )
    args = parser.parse_args()

    paths.setup(args.data_dir)
    db = Database(paths.db_path())

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setWindowIcon(make_app_icon())
    app.setQuitOnLastWindowClosed(False)

    # 首次启动：设置身份
    if db.get_identity() is None:
        dlg = LoginDialog()
        if dlg.exec() != LoginDialog.DialogCode.Accepted or not dlg.user_name():
            return 0
        db.set_identity(dlg.user_name())

    ctx = AppContext(db)
    win = MainWindow(ctx)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
