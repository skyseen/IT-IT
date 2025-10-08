"""PySide6 prototype UI illustrating a beauty-tech direction for IT-IT."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict

from PySide6 import QtCore, QtWidgets

from activity_log import get_recent_events, log_event
from config_manager import get_active_profile_name


@dataclass
class CommandAction:
    """Encapsulates a command card's copy and handler."""

    label: str
    description: str
    handler: Callable[[QtWidgets.QWidget], None]
    accent: str = "#8AA7FF"


class CommandCard(QtWidgets.QFrame):
    """Visually-rich card to surface an automation workflow."""

    def __init__(self, action: CommandAction, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commandCard")
        self.setProperty("accent", action.accent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QtWidgets.QLabel(action.label)
        title.setObjectName("cardTitle")
        body = QtWidgets.QLabel(action.description)
        body.setObjectName("cardBody")
        body.setWordWrap(True)

        cta = QtWidgets.QPushButton("Launch")
        cta.setObjectName("cardCta")
        cta.clicked.connect(lambda: action.handler(self))

        layout.addWidget(title)
        layout.addWidget(body, 1)
        layout.addWidget(cta)


class ActivityFeed(QtWidgets.QGroupBox):
    """Lightweight activity feed powered by the existing log storage."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Operations Center", parent)
        self.setObjectName("activityFeed")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setObjectName("activityList")
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget, 1)

        refresh = QtWidgets.QPushButton("Refresh Feed")
        refresh.setObjectName("refreshButton")
        refresh.clicked.connect(self.populate)
        layout.addWidget(refresh)

        self.populate()

    def populate(self) -> None:
        self.list_widget.clear()
        for event in get_recent_events(limit=12):
            timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M")
            self.list_widget.addItem(f"[{timestamp}] {event.summary}")


class MainWindow(QtWidgets.QMainWindow):
    """Beauty-tech inspired PySide6 shell for IT-IT."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IT ! IT – Beauty Tech Edition")
        self.resize(1200, 780)

        container = QtWidgets.QWidget()
        container.setObjectName("appContainer")
        self.setCentralWidget(container)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(28)

        header = self._build_header(container)
        layout.addWidget(header)

        tabs = QtWidgets.QTabWidget()
        tabs.setObjectName("mainTabs")
        tabs.addTab(self._build_user_ops_tab(), "User Ops")
        tabs.addTab(self._build_placeholder_tab("SAP"), "SAP")
        tabs.addTab(self._build_placeholder_tab("Agile"), "Agile")
        tabs.addTab(self._build_placeholder_tab("Telecom"), "Telecom")
        tabs.addTab(ActivityFeed(), "Operations Center")
        layout.addWidget(tabs, 1)

    def _build_header(self, parent: QtWidgets.QWidget) -> QtWidgets.QWidget:
        header = QtWidgets.QFrame(parent)
        header.setObjectName("heroHeader")
        grid = QtWidgets.QGridLayout(header)
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setHorizontalSpacing(36)
        grid.setVerticalSpacing(12)

        banner = QtWidgets.QLabel("IT ! IT Admin Toolkit")
        banner.setObjectName("heroTitle")
        sub = QtWidgets.QLabel(
            "Collaborative automation cockpit with a luminous beauty-tech polish."
        )
        sub.setObjectName("heroSubtitle")
        sub.setWordWrap(True)

        badge = QtWidgets.QLabel()
        badge.setObjectName("statusBadge")
        badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        badge.setText(f"● {get_active_profile_name()} • Ready")

        grid.addWidget(banner, 0, 0, 1, 1)
        grid.addWidget(sub, 1, 0, 1, 1)
        grid.addWidget(badge, 0, 1, 2, 1)
        return header

    def _build_user_ops_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(tab)
        layout.setSpacing(22)
        layout.setContentsMargins(12, 12, 12, 12)

        actions: Dict[str, CommandAction] = {
            "new_user": CommandAction(
                label="Create New User Pack",
                description=(
                    "Bundle welcome assets, verify provisioning data, and prepare the "
                    "beauty-tech onboarding email sequence."
                ),
                handler=lambda parent: log_event("prototype", "Trigger new user dialog"),
                accent="#7CC3A2",
            ),
            "disable_user": CommandAction(
                label="Disable User Access",
                description="Queue graceful off-boarding notices and archive instructions for ops.",
                handler=lambda parent: log_event("prototype", "Trigger disable dialog"),
                accent="#E69896",
            ),
            "agile_reset": CommandAction(
                label="Reset Agile Credentials",
                description="Kick off the Agile password reset concierge flow with ticket tracking.",
                handler=lambda parent: log_event("prototype", "Trigger agile reset"),
            ),
            "sap_creation": CommandAction(
                label="Process SAP S4 Onboarding",
                description="Review consolidated sheets and send tailored SAP onboarding comms.",
                handler=lambda parent: log_event("prototype", "Trigger SAP onboarding"),
                accent="#9E8CFF",
            ),
        }

        row = 0
        col = 0
        for action in actions.values():
            card = CommandCard(action)
            layout.addWidget(card, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)
        return tab

    def _build_placeholder_tab(self, label: str) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        message = QtWidgets.QLabel(
            f"Qt prototype placeholder for {label} workflows.\n\n"
            "Port existing Tkinter dialogs one-by-one to PySide6 to fully replace the UI."
        )
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message.setObjectName("placeholderText")
        message.setWordWrap(True)
        layout.addWidget(message, 1)
        return tab


def launch() -> None:
    """Launch the PySide6 prototype."""

    app = QtWidgets.QApplication([])
    theme_path = Path(__file__).with_name("pyside6_theme.qss")
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text())
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch()
