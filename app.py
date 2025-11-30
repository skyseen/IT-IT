"""IT!IT Application with Sidebar Layout - Main Entry Point."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Callable, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from activity_log import describe_event, get_recent_events, log_event, register_listener
from config_manager import get_active_profile_name
from sidebar_layout import ContentContainer, Sidebar, TopBar
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

# Import Kanban UI
try:
    from kanban.ui_board import build_kanban_section
    KANBAN_AVAILABLE = True
except Exception as e:
    print(f"Warning: Kanban module failed to load: {e}")
    import traceback
    traceback.print_exc()
    KANBAN_AVAILABLE = False


class ActivityPanel(QtWidgets.QGroupBox):
    """Activity log panel."""
    
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


class MainWindow(QtWidgets.QMainWindow):
    """Main application window with sidebar navigation."""
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("IT!IT – OA Systems Operator Console")
        self.setMinimumSize(1280, 720)  # Responsive minimum
        self.resize(1600, 900)  # Default size

        # Set window icon
        icon_path = "logo.png"
        if Path(icon_path).exists():
            self.setWindowIcon(QtGui.QIcon(icon_path))

        # Main layout with sidebar
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar (no menu toggle button)
        self.top_bar = TopBar()
        self.top_bar.settings_requested.connect(self.open_settings)
        main_layout.addWidget(self.top_bar)

        # Content area with sidebar
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar (starts collapsed at 50px)
        self.sidebar = Sidebar()
        self.sidebar.setMinimumWidth(50)
        self.sidebar.setMaximumWidth(50)
        self.sidebar.section_changed.connect(self._on_section_changed)
        content_layout.addWidget(self.sidebar)

        # Content container
        self.content = ContentContainer()
        content_layout.addWidget(self.content, 1)

        content_widget = QtWidgets.QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)

        # Build sections
        self._build_sections()

        # Status bar
        status_bar = QtWidgets.QStatusBar()
        status_bar.setStyleSheet(
            f"background-color: rgba(15, 23, 42, 0.92); color: {TEXT_MUTED}; font-size: 11px;"
        )
        self.setStatusBar(status_bar)

        self.environment_label = QtWidgets.QLabel()
        self.environment_label.setStyleSheet(f"color: {SUCCESS}; font-weight: 600;")
        self.status_message = QtWidgets.QLabel("Ready")
        self.status_message.setStyleSheet(f"color: {TEXT_PRIMARY};")
        hint_label = QtWidgets.QLabel("Esc: Exit • ⚙: Settings • Ctrl+1-7: Quick Nav")
        hint_label.setStyleSheet(f"color: {TEXT_MUTED};")
        status_bar.addPermanentWidget(hint_label)
        status_bar.addWidget(self.environment_label)
        status_bar.addWidget(self.status_message, 1)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        self._update_environment()

        register_listener(self.on_log_event)
        log_event("ui", "Operator console launched (new layout)", details={"profile": get_active_profile_name()})

        # Set default section to Kanban
        if KANBAN_AVAILABLE:
            self.sidebar.set_active_section("kanban")
            self.content.show_section("kanban")
        else:
            self.sidebar.set_active_section("user_mgmt")
            self.content.show_section("user_mgmt")

    def _build_sections(self) -> None:
        """Build all content sections."""
        # Kanban (main feature)
        if KANBAN_AVAILABLE:
            self.content.add_section("kanban", build_kanban_section)
            
        # My Tasks view (placeholder for now - will link to Kanban My Tasks)
        def build_my_tasks(parent):
            layout = QtWidgets.QVBoxLayout(parent)
            label = QtWidgets.QLabel("📊 My Tasks\n\nGo to Kanban → My Tasks tab")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 16px;")
            layout.addWidget(label)
        self.content.add_section("my_tasks", build_my_tasks)
        
        # Admin Panel (placeholder)
        def build_admin(parent):
            layout = QtWidgets.QVBoxLayout(parent)
            label = QtWidgets.QLabel("⚙️ Admin Panel\n\nComing soon...")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 16px;")
            layout.addWidget(label)
        self.content.add_section("admin", build_admin)
        
        # User Management
        self.content.add_section("user_mgmt", build_user_management_section)
        
        # SAP Tools
        self.content.add_section("sap", build_sap_section)
        
        # Agile Tools
        self.content.add_section("agile", build_agile_section)
        
        # Telco Tools
        self.content.add_section("telco", build_telco_section)
        
        # Operations Center (Activity Log)
        def build_operations(parent):
            layout = QtWidgets.QVBoxLayout(parent)
            layout.setContentsMargins(20, 20, 20, 20)
            self.activity_panel = ActivityPanel()
            layout.addWidget(self.activity_panel)
        self.content.add_section("operations", build_operations)
        
        # Settings (will show dialog)
        # No content needed, handled in _on_section_changed

    def _on_section_changed(self, section_id: str):
        """Handle section change."""
        if section_id == "settings":
            # Show settings dialog instead of section
            self.open_settings()
            # Keep current section active
            return
        
        self.content.show_section(section_id)
        self.status_message.setText(f"Switched to {self._get_section_name(section_id)}")
        
    def _get_section_name(self, section_id: str) -> str:
        """Get friendly name for section."""
        names = {
            "kanban": "Kanban Board",
            "my_tasks": "My Tasks",
            "admin": "Admin Panel",
            "user_mgmt": "User Management",
            "sap": "SAP Tools",
            "agile": "Agile Tools",
            "telco": "Telco Tools",
            "operations": "Operations Center",
            "settings": "Settings"
        }
        return names.get(section_id, section_id.title())

    # Sidebar is now always icon-only (no toggle needed)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Navigation shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self, activated=lambda: self._switch_to("kanban"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self, activated=lambda: self._switch_to("my_tasks"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self, activated=lambda: self._switch_to("user_mgmt"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+4"), self, activated=lambda: self._switch_to("sap"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+5"), self, activated=lambda: self._switch_to("agile"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+6"), self, activated=lambda: self._switch_to("telco"))
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+7"), self, activated=lambda: self._switch_to("operations"))
        
        # Settings
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+,"), self, activated=self.open_settings)
        
        # Exit
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Escape), self, activated=self.close)
        
    def _switch_to(self, section_id: str):
        """Switch to a section programmatically."""
        self.sidebar.set_active_section(section_id)
        self.content.show_section(section_id)

    def _update_environment(self) -> None:
        """Update environment label."""
        profile = get_active_profile_name()
        self.environment_label.setText(f"Environment: {profile}")
        self.top_bar.set_environment(profile)

    def on_log_event(self, entry: dict) -> None:
        """Handle log events."""
        self.status_message.setText(describe_event(entry))
        if hasattr(self, 'activity_panel') and self.activity_panel:
            self.activity_panel.append(entry)

    def open_settings(self) -> None:
        """Open settings dialog."""
        show_settings_dialog(self)
        self._update_environment()

    def resizeEvent(self, event):
        """Handle window resize for responsive behavior."""
        super().resizeEvent(event)
        # Sidebar is now always collapsed by default and expands on hover
        # No need for auto-collapse based on window size


def launch() -> None:
    """Launch the application."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    apply_dark_tech_palette(app)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    launch()

