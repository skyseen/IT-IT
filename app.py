from __future__ import annotations

import datetime
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
                ,----,   ,---,                 ,----, 
              ,/   .`|,`--.' |               ,/   .`| 
   ,---,    ,`   .'  :|   :  :    ,---,    ,`   .'  : 
,`--.' |  ;    ;     /'   '  ; ,`--.' |  ;    ;     / 
|   :  :.'___,/    ,' |   |  | |   :  :.'___,/    ,'  
:   |  '|    :     |  '   :  ; :   |  '|    :     |   
|   :  |;    |.';  ;  |   |  ' |   :  |;    |.';  ;   
'   '  ;`----'  |  |  '   :  | '   '  ;`----'  |  |   
|   |  |    '   :  ;  ;   |  ; |   |  |    '   :  ;   
'   :  ;    |   |  '  `---'. | '   :  ;    |   |  '   
|   |  '    '   :  |   `--..`; |   |  '    '   :  |   
'   :  |    ;   |.'   .--,_    '   :  |    ;   |.'    
;   |.'     '---'     |    |`. ;   |.'     '---'      
'---'                 `-- -`, ;'---'                  
                        '---`"                       
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

        # Logo on the left
        logo_container = QtWidgets.QWidget()
        logo_layout = QtWidgets.QVBoxLayout(logo_container)
        logo_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(4)
        
        # Create a styled logo box
        logo_frame = QtWidgets.QFrame()
        logo_frame.setFixedSize(160, 160)
        logo_frame.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(56, 189, 248, 0.15),
                    stop:1 rgba(99, 102, 241, 0.15));
                border: 2px solid {ACCENT};
                border-radius: 20px;
            }}
            """
        )
        
        logo_text = QtWidgets.QLabel("IT!IT")
        logo_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(
            f"background: transparent; color: {ACCENT}; "
            "font-size: 48px; font-weight: 900; letter-spacing: -0.02em;"
        )
        
        logo_frame_layout = QtWidgets.QVBoxLayout(logo_frame)
        logo_frame_layout.addWidget(logo_text)
        logo_layout.addWidget(logo_frame)
        
        oa_label = QtWidgets.QLabel("OA Tool")
        oa_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        oa_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 13px; font-weight: 600; "
            "letter-spacing: 0.15em; background: transparent;"
        )
        logo_layout.addWidget(oa_label)

        # Title and subtitle
        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)
        title_layout.setSpacing(8)
        
        title = QtWidgets.QLabel("IT!IT Automation")
        title.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: 0.02em;")
        title_layout.addWidget(title)

        subtitle = QtWidgets.QLabel("Collab with Codex&Claude")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px; letter-spacing: 0.08em;")
        title_layout.addWidget(subtitle)
        title_layout.addStretch()

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
            f"background-color: {ACCENT}; color: #051221; font-weight: 700; padding: 12px 18px; border-radius: 10px;"
        )
        self.settings_button.clicked.connect(self.settings_requested.emit)

        layout.addWidget(logo_container, 0, 0, 3, 1)
        layout.addWidget(title_container, 0, 1, 2, 1)
        layout.addWidget(self.status_badge, 0, 2, 2, 1)
        layout.addWidget(self.settings_button, 2, 2)

    def update_badge(self, profile: str) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.status_badge.setText(f"● {profile} • {now}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IT!IT OA Tool")
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
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 12px;
                background-color: rgba(15, 23, 42, 0.6);
            }}
            QTabBar::tab {{
                background-color: rgba(30, 41, 59, 0.8);
                color: {TEXT_MUTED};
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT};
                color: #051221;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: rgba(56, 189, 248, 0.2);
                color: {TEXT_PRIMARY};
            }}
            """
        )
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

        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Escape), self, activated=self.close)

    def _build_tabs(self) -> None:
        def create_tab(builder: Callable[[QtWidgets.QWidget], None]) -> QtWidgets.QWidget:
            tab = QtWidgets.QWidget()
            builder(tab)
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


def launch() -> None:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    apply_dark_tech_palette(app)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch()
