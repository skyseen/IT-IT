"""Sidebar navigation component for IT!IT application."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6 import QtCore, QtGui, QtWidgets

# Color constants
SURFACE_BG = "#0F172A"
ELEVATED_BG = "#1E293B"
CARD_BG = "#334155"
HOVER_BG = "#475569"
ACCENT = "#38BDF8"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "rgba(56, 189, 248, 0.2)"


class SidebarButton(QtWidgets.QWidget):
    """A sidebar navigation button with icon and label."""
    
    clicked = QtCore.Signal(str)  # Emits the section ID
    
    def __init__(
        self,
        section_id: str,
        icon: str,
        label: str,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(parent)
        self.section_id = section_id
        self.icon = icon
        self.label_text = label
        self.is_active = False
        self.is_separator = False
        
        self.setFixedHeight(44)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setToolTip(label)  # Show label as tooltip when collapsed
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the button UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Icon label
        self.icon_label = QtWidgets.QLabel(self.icon)
        self.icon_label.setFixedWidth(44)  # Full width for centering
        self.icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {TEXT_MUTED};
            }}
        """)
        layout.addWidget(self.icon_label)
        
        # Text label
        self.text_label = QtWidgets.QLabel(self.label_text)
        self.text_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {TEXT_MUTED};
            }}
        """)
        layout.addWidget(self.text_label, 1)
        
        self._update_style()
        
    def set_active(self, active: bool):
        """Set the active state of the button."""
        self.is_active = active
        self._update_style()
        
    def set_collapsed(self, collapsed: bool):
        """Show/hide the text label."""
        self.text_label.setVisible(not collapsed)
        
    def _update_style(self):
        """Update the button styling."""
        if self.is_active:
            bg_color = ELEVATED_BG  # Blend with background
            border_style = f"border-left: 3px solid {ACCENT};"
            icon_color = ACCENT
            text_color = TEXT_PRIMARY
        else:
            bg_color = ELEVATED_BG  # Same as background
            border_style = "border-left: 3px solid transparent;"
            icon_color = TEXT_MUTED
            text_color = TEXT_MUTED
            
        self.setStyleSheet(f"""
            SidebarButton {{
                background-color: {bg_color};
                border-radius: 6px;
                {border_style}
            }}
            SidebarButton:hover {{
                background-color: rgba(56, 189, 248, 0.06);
            }}
        """)
        
        self.icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {icon_color};
            }}
        """)
        
        self.text_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {text_color};
            }}
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.section_id)
        super().mousePressEvent(event)


class SidebarSeparator(QtWidgets.QFrame):
    """A visual separator in the sidebar."""
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BORDER_COLOR};
                border: none;
                margin: 8px 12px;
            }}
        """)


class Sidebar(QtWidgets.QFrame):
    """Collapsible sidebar navigation."""
    
    section_changed = QtCore.Signal(str)  # Emits section ID when changed
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.is_collapsed = True  # Always collapsed (icon-only mode)
        self.buttons = {}
        self.current_section = None
        
        self.setObjectName("sidebar")
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the sidebar UI."""
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {ELEVATED_BG};
                border-right: 1px solid {BORDER_COLOR};
            }}
            QScrollArea {{
                background-color: {ELEVATED_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                width: 0px;  /* Hide scrollbar */
                background: transparent;
            }}
        """)
        
        # Create scroll area for vertical scrolling
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container widget for buttons
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(2)
        
        # Add navigation items (Kanban first!)
        self.add_button("kanban", "📋", "Kanban Board", layout)
        layout.addWidget(SidebarSeparator())
        
        # Other tools
        self.add_button("user_mgmt", "👥", "User Management", layout)
        self.add_button("sap", "💼", "SAP Tools", layout)
        self.add_button("agile", "🎫", "Agile Tools", layout)
        self.add_button("telco", "📞", "Telco Tools", layout)
        self.add_button("operations", "📋", "Operations Center", layout)
        
        layout.addStretch()
        
        layout.addWidget(SidebarSeparator())
        self.add_button("settings", "🔧", "Settings", layout)
        
        scroll_area.setWidget(container)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
    def add_button(self, section_id: str, icon: str, label: str, layout):
        """Add a navigation button."""
        button = SidebarButton(section_id, icon, label)
        button.clicked.connect(self._on_button_clicked)
        button.set_collapsed(True)  # Always collapsed (icon-only)
        layout.addWidget(button)
        self.buttons[section_id] = button
        
    def get_width(self) -> int:
        """Get current width (expanded or collapsed)."""
        return 50 if self.is_collapsed else 200
        
    def _on_button_clicked(self, section_id: str):
        """Handle button click."""
        self.set_active_section(section_id)
        self.section_changed.emit(section_id)
        
    def set_active_section(self, section_id: str):
        """Set the active section."""
        self.current_section = section_id
        for btn_id, button in self.buttons.items():
            button.set_active(btn_id == section_id)
            
    # Sidebar is now always collapsed (icon-only mode)


class TopBar(QtWidgets.QFrame):
    """Top navigation bar."""
    
    settings_requested = QtCore.Signal()
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setObjectName("topBar")
        self.setFixedHeight(40)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the top bar UI."""
        self.setStyleSheet(f"""
            QFrame#topBar {{
                background-color: {SURFACE_BG};
                border-bottom: 1px solid {BORDER_COLOR};
            }}
        """)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)
        
        # App title (no menu button)
        title = QtWidgets.QLabel("IT!IT")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 700;
                color: {ACCENT};
            }}
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Environment indicator
        self.env_label = QtWidgets.QLabel("[Production]")
        self.env_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 600;
                color: {TEXT_MUTED};
                padding: 6px 12px;
                background-color: {ELEVATED_BG};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.env_label)
        
        # User info
        self.user_btn = QtWidgets.QPushButton("👤 User")
        self.user_btn.setFixedHeight(32)
        self.user_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.user_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ELEVATED_BG};
                color: {TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
                border: 1px solid transparent;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
                border-color: {ACCENT};
            }}
        """)
        layout.addWidget(self.user_btn)
        
        # Settings button
        settings_btn = QtWidgets.QPushButton("⚙️")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_PRIMARY};
                font-size: 16px;
                border: 1px solid transparent;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {HOVER_BG};
                border-color: {ACCENT};
            }}
        """)
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)
        
    def set_environment(self, env: str):
        """Set the environment label."""
        self.env_label.setText(f"[{env}]")


class ContentContainer(QtWidgets.QWidget):
    """Container for the main content area."""
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.sections = {}
        self.current_section = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the content container."""
        self.stack = QtWidgets.QStackedWidget()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)
        
    def add_section(
        self,
        section_id: str,
        builder: Callable[[QtWidgets.QWidget], None]
    ):
        """Add a content section."""
        widget = QtWidgets.QWidget()
        builder(widget)
        self.stack.addWidget(widget)
        self.sections[section_id] = widget
        
    def show_section(self, section_id: str):
        """Show a specific section."""
        if section_id in self.sections:
            self.current_section = section_id
            self.stack.setCurrentWidget(self.sections[section_id])

