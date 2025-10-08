from __future__ import annotations

import datetime
import sys
from typing import Callable, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from activity_log import describe_event, get_recent_events, log_event, register_listener
from config_manager import get_active_profile_name
from ui import (
    ACCENT,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    apply_dark_tech_palette,
    build_agile_section,
    build_sap_section,
    build_telco_section,
    build_user_management_section,
    show_settings_dialog,
)

ASCII_BANNER = """
██╗████████╗    ██╗ ██████╗     ██╗████████╗
██║╚══██╔══╝    ██║██╔════╝     ██║╚══██╔══╝
██║   ██║       ██║██║  ███╗    ██║   ██║   
██║   ██║  ██   ██║██║   ██║    ██║   ██║   
██║   ██║  ╚█████╔╝╚██████╔╝    ██║   ██║   
╚═╝   ╚═╝   ╚════╝  ╚═════╝     ╚═╝   ╚═╝   
"""


class ActivityPanel(QtWidgets.QGroupBox):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__("Operations Center", parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.text.setPlaceholderText("Activity log will appear here…")
        layout.addWidget(self.text, 1)

        refresh = QtWidgets.QPushButton("Refresh Feed")
        refresh.clicked.connect(self.refresh)
        layout.addWidget(refresh)

        self.refresh()

    def refresh(self) -> None:
        events = get_recent_events(limit=120)
        lines = [describe_event(entry) for entry in events]
        self.text.setPlainText("\n".join(lines))
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())

    def append(self, entry: dict) -> None:
        cursor = self.text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertText(describe_event(entry) + "\n")
        self.text.setTextCursor(cursor)
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())


class HeroHeader(QtWidgets.QFrame):
    settings_requested = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("heroHeader")
        self.setStyleSheet(
            """
            QFrame#heroHeader {
                background-color: rgba(20, 36, 59, 0.72);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 24px;
            }
            """
        )

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setHorizontalSpacing(32)
        layout.setVerticalSpacing(12)

        banner = QtWidgets.QLabel(ASCII_BANNER)
        banner.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        banner.setStyleSheet("font-family: 'Fira Code', 'Consolas'; font-size: 11px; color: rgba(148, 163, 184, 0.75);")

        title = QtWidgets.QLabel("IT ! IT Automation Cockpit")
        title.setStyleSheet("font-size: 26px; font-weight: 700; letter-spacing: 0.04em;")

        subtitle = QtWidgets.QLabel(
            "Dark-tech control center for orchestrating onboarding, SAP, Agile, and telco workflows."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; letter-spacing: 0.06em;")

        self.status_badge = QtWidgets.QLabel()
        self.status_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setMinimumWidth(220)
        self.status_badge.setStyleSheet(
            f"background-color: rgba(56, 189, 248, 0.12); color: {ACCENT}; padding: 12px 16px;"
            "border-radius: 16px; font-weight: 600;"
        )

        self.settings_button = QtWidgets.QPushButton("⚙ Settings")
        self.settings_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.settings_button.setStyleSheet(
            f"background-color: {ACCENT}; color: #051221; font-weight: 700; padding: 12px 18px;"
        )
        self.settings_button.clicked.connect(self.settings_requested.emit)

        layout.addWidget(banner, 0, 0, 2, 1)
        layout.addWidget(title, 0, 1)
        layout.addWidget(subtitle, 1, 1)
        layout.addWidget(self.status_badge, 0, 2, 2, 1)
        layout.addWidget(self.settings_button, 2, 2)

    def update_badge(self, profile: str) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.status_badge.setText(f"● {profile} • {now}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IT ! IT – Dark Tech Edition")
        self.resize(1240, 820)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root_layout = QtWidgets.QVBoxLayout(central)
        root_layout.setContentsMargins(32, 28, 32, 24)
        root_layout.setSpacing(24)

        self.header = HeroHeader()
        self.header.settings_requested.connect(self.open_settings)
        root_layout.addWidget(self.header)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        root_layout.addWidget(self.tabs, 1)

        self._build_tabs()

        self.activity_panel = ActivityPanel()
        self.tabs.addTab(self.activity_panel, "Operations Center")

        status_bar = QtWidgets.QStatusBar()
        status_bar.setStyleSheet(
            f"background-color: rgba(15, 23, 42, 0.92); color: {TEXT_MUTED}; font-size: 11px;"
        )
        self.setStatusBar(status_bar)

        self.environment_label = QtWidgets.QLabel()
        self.environment_label.setStyleSheet(f"color: {SUCCESS}; font-weight: 600;")
        self.status_message = QtWidgets.QLabel("Ready")
        self.status_message.setStyleSheet(f"color: {TEXT_PRIMARY};")
        hint_label = QtWidgets.QLabel("Press Esc to exit • Use ⚙ Settings to manage configuration")
        hint_label.setStyleSheet(f"color: {TEXT_MUTED};")
        status_bar.addPermanentWidget(hint_label)
        status_bar.addWidget(self.environment_label)
        status_bar.addWidget(self.status_message, 1)

        self._update_environment()
        self._refresh_badge()
        self._badge_timer = QtCore.QTimer(self)
        self._badge_timer.timeout.connect(self._refresh_badge)
        self._badge_timer.start(60000)

        register_listener(self.on_log_event)
        log_event("ui", "Operator console launched", details={"profile": get_active_profile_name()})

        self._escape_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key.Key_Escape), self
        )
        self._escape_shortcut.activated.connect(self.close)

    def _build_tabs(self) -> None:
        def create_tab(builder: Callable[[QtWidgets.QWidget], None]) -> QtWidgets.QWidget:
            tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(tab)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(18)
            inner = QtWidgets.QWidget()
            inner_layout = QtWidgets.QVBoxLayout(inner)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            builder(inner)
            layout.addWidget(inner)
            return tab

        self.tabs.addTab(create_tab(build_user_management_section), "User Ops")
        self.tabs.addTab(create_tab(build_sap_section), "SAP")
        self.tabs.addTab(create_tab(build_agile_section), "Agile")
        self.tabs.addTab(create_tab(build_telco_section), "Telecom")

    def _update_environment(self) -> None:
        profile = get_active_profile_name()
        self.environment_label.setText(f"Environment: {profile}")

    def _refresh_badge(self) -> None:
        self.header.update_badge(get_active_profile_name())

    def on_log_event(self, entry: dict) -> None:
        self.status_message.setText(describe_event(entry))
        self.activity_panel.append(entry)

    def open_settings(self) -> None:
        show_settings_dialog(self)
        self._update_environment()
        self._refresh_badge()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        log_event("ui", "Operator console closed", details={"profile": get_active_profile_name()})
        super().closeEvent(event)


_WINDOW: Optional[MainWindow] = None


def launch() -> int:
    global _WINDOW

    existing_app = QtWidgets.QApplication.instance()
    owns_app = existing_app is None

    if owns_app:
        QtCore.QCoreApplication.setAttribute(
            QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True
        )
        QtCore.QCoreApplication.setAttribute(
            QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
        )
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = existing_app

    apply_dark_tech_palette(app)

    _WINDOW = MainWindow()
    _WINDOW.show()
    _WINDOW.raise_()
    _WINDOW.activateWindow()

    if owns_app:
        result = app.exec()
        _WINDOW = None
        return result

    return 0


if __name__ == "__main__":
    raise SystemExit(launch())
