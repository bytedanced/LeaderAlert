"""主窗口：左侧导航 + 右侧堆叠页面（仪表盘/在线/报警/牛管理/设置）。"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

import config
from ui.pages.alerts_page import AlertsPage
from ui.pages.dashboard import DashboardPage
from ui.pages.peers_page import PeersPage
from ui.pages.settings_page import SettingsPage
from ui.pages.targets_page import TargetsPage


class MainWindow(QMainWindow):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle(f"牛来了预警 v{config.APP_VERSION}")
        self.resize(1080, 720)
        self._tray_tipped = False

        # ---------- 侧边导航 ----------
        nav = QWidget()
        nav.setObjectName("sideNav")
        nav.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 12)
        nav_layout.setSpacing(2)

        logo = QLabel("🐮 牛来了预警")
        logo.setObjectName("navLogo")
        identity = QLabel(f"{ctx.user}@{ctx.host}")
        identity.setObjectName("navIdentity")
        identity.setWordWrap(True)
        nav_layout.addWidget(logo)
        nav_layout.addWidget(identity)

        self._nav_buttons = []
        self._stack = QStackedWidget()

        self._dashboard = DashboardPage(ctx)
        self._peers = PeersPage(ctx)
        self._alerts = AlertsPage(ctx)
        self._targets = TargetsPage(ctx)
        self._settings = SettingsPage(ctx, on_saved=self._on_settings_saved)
        pages = [
            ("仪表盘", self._dashboard),
            ("在线人员", self._peers),
            ("报警历史", self._alerts),
            ("牛管理", self._targets),
            ("设置", self._settings),
        ]
        for i, (name, page) in enumerate(pages):
            btn = QPushButton(name)
            btn.setProperty("navItem", True)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _c=False, idx=i: self._switch(idx))
            nav_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self._stack.addWidget(page)
        nav_layout.addStretch(1)

        version = QLabel(f"v{config.APP_VERSION}")
        version.setObjectName("navIdentity")
        version.setStyleSheet("padding: 0 16px;")
        nav_layout.addWidget(version)

        # ---------- 组装 ----------
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(nav)
        root.addWidget(self._stack, 1)
        self.setCentralWidget(central)

        # ---------- 状态栏 ----------
        status = QStatusBar()
        self._status_udp = QLabel("UDP：等待心跳...")
        self._status_cooldown = QLabel("")
        status.addWidget(self._status_udp)
        status.addPermanentWidget(self._status_cooldown)
        self.setStatusBar(status)

        # ---------- 信号 ----------
        ctx.detector.alert_confirmed.connect(ctx.submit_local_alert)
        ctx.alerts_changed.connect(self._on_alerts_changed)

        # ---------- 定时刷新 ----------
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start()

        self._setup_tray()
        self._switch(0)

    # ---------- 导航 ----------
    def _switch(self, index):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        # 切到对应页时刷新数据
        page = self._stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()
        elif hasattr(page, "refresh_stats"):
            page.refresh_stats()

    # ---------- 托盘 ----------
    def _setup_tray(self):
        menu = QMenu()
        act_show = menu.addAction("显示主窗口")
        act_quit = menu.addAction("退出")
        act_show.triggered.connect(self.show_and_raise)
        act_quit.triggered.connect(self._quit)
        self.ctx.tray.setContextMenu(menu)
        self.ctx.tray.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_and_raise()

    def show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---------- 事件 ----------
    def _on_settings_saved(self, old_camera):
        self._dashboard.restart_if_camera_changed(old_camera)
        self._dashboard.refresh_stats()

    def _on_alerts_changed(self):
        # 报警后若在仪表盘页，统计卡同步刷新
        self._dashboard.refresh_stats()

    def _on_timer(self):
        self.ctx.prune_peers()
        if self._stack.currentWidget() is self._dashboard:
            self._dashboard.refresh_stats()
        left = self.ctx.cooldown_left()
        self._status_cooldown.setText(f"报警冷却中：剩 {left}s" if left > 0 else "")
        if self.ctx.udp_ok and self._status_udp.text() != "UDP：正常":
            self._status_udp.setText("UDP：正常")

    # ---------- 关闭行为 ----------
    def closeEvent(self, event):
        """关闭窗口 → 最小化到托盘，程序继续运行。"""
        event.ignore()
        self.hide()
        if not self._tray_tipped:
            self._tray_tipped = True
            self.ctx.tray.showMessage(
                "程序在后台运行",
                "主窗口已最小化到托盘，双击托盘图标可重新打开；退出请通过托盘菜单。",
            )

    def _quit(self):
        self.ctx.shutdown()
        from PySide6.QtWidgets import QApplication

        QApplication.quit()
