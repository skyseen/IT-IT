"""Main Kanban board UI component."""

from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from config_manager import (
    get_active_profile_name,
    get_remembered_kanban_session_token,
    set_remembered_kanban_session_token,
)
from kanban.auth import AuthResult, logout, resume_session, update_last_activity
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.ui_components import AdminPasswordResetDialog, ChangePasswordDialog, LoginDialog

# Import color constants from ui.py
try:
    from ui import ACCENT, CARD_BG, ELEVATED_BG, INFO, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, WARNING, SURFACE_BG
except ImportError:
    # Fallback if ui.py is not available
    ACCENT = "#38BDF8"
    CARD_BG = "#1E293B"
    ELEVATED_BG = "#334155"
    SURFACE_BG = "#0F172A"
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    SUCCESS = "#34D399"
    WARNING = "#FBBF24"
    INFO = "#60A5FA"


class DraggableTaskCard(QtWidgets.QFrame):
    """A draggable task card widget."""
    
    clicked = QtCore.Signal(int)  # Emits task_id when clicked
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_id = task.id
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the card UI."""
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
                padding: 8px;
            }}
            QFrame:hover {{
                border-color: {ACCENT};
                background-color: {ELEVATED_BG};
            }}
            """
        )
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
    def mousePressEvent(self, event):
        """Handle mouse press - start drag or click."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move - initiate drag."""
        if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return
            
        # Create drag
        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()
        mime_data.setText(str(self.task_id))
        drag.setMimeData(mime_data)
        
        # Create drag pixmap (preview)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(200, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        drag.setHotSpot(event.pos())
        
        # Execute drag
        drag.exec(QtCore.Qt.DropAction.MoveAction)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release - emit click if not dragging."""
        try:
            if hasattr(self, 'drag_start_position'):
                if (event.pos() - self.drag_start_position).manhattanLength() < QtWidgets.QApplication.startDragDistance():
                    self.clicked.emit(self.task_id)
            super().mouseReleaseEvent(event)
        except RuntimeError:
            # Widget was deleted during drag operation, ignore
            pass


class DropZoneColumn(QtWidgets.QFrame):
    """A column that accepts dropped task cards."""
    
    task_dropped = QtCore.Signal(int, int)  # Emits (task_id, column_id)
    
    def __init__(self, column_id, parent=None):
        super().__init__(parent)
        self.column_id = column_id
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        """Accept drag enter."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Highlight column
            self.setStyleSheet(
                self.styleSheet() + """
                QFrame {
                    border: 2px solid #38BDF8 !important;
                    background-color: rgba(56, 189, 248, 0.1) !important;
                }
                """
            )
    
    def dragMoveEvent(self, event):
        """Accept drag move to allow dropping."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            
    def dragLeaveEvent(self, event):
        """Remove highlight when drag leaves."""
        # Reset styling
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 12px;
            }}
            """
        )
        
    def dropEvent(self, event):
        """Handle drop - emit signal."""
        task_id = int(event.mimeData().text())
        self.task_dropped.emit(task_id, self.column_id)
        event.acceptProposedAction()
        
        # Reset styling
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 12px;
            }}
            """
        )


class KanbanBoardWidget(QtWidgets.QWidget):
    """Main Kanban board widget displaying columns and task cards."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.db = None
        self.manager = None
        self.auth_result: AuthResult | None = None
        self.columns = []
        self.column_widgets = {}
        self.account_button: QtWidgets.QToolButton | None = None
        self.account_menu: QtWidgets.QMenu | None = None
        self.admin_reset_action: QtGui.QAction | None = None
        self.change_password_action: QtGui.QAction | None = None
        self.switch_user_action: QtGui.QAction | None = None
        self.sign_out_action: QtGui.QAction | None = None
        self._last_username: str | None = None
        
        # Auto-refresh timer
        self.auto_refresh_timer = QtCore.QTimer(self)
        self.auto_refresh_timer.setInterval(30000)  # 30 seconds
        self.auto_refresh_timer.timeout.connect(self._auto_refresh)

        self._init_database()
        self._init_ui()
        QtCore.QTimer.singleShot(0, self._attempt_initial_login)

    def _init_database(self) -> None:
        """Initialize database connection and manager."""
        try:
            self.db = get_db_manager()
            if not self.db.test_connection():
                self._show_error("Database connection failed!")
                return

        except Exception as e:
            self._show_error(f"Database initialization failed: {e}")

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)

        # Tab widget for Board / My Tasks / Reports
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {SURFACE_BG};
            }}
            QTabBar::tab {{
                background: {ELEVATED_BG};
                color: {TEXT_MUTED};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {CARD_BG};
                color: {ACCENT};
            }}
            QTabBar::tab:hover {{
                background: {CARD_BG};
                color: {TEXT_PRIMARY};
            }}
        """)

        # Board tab (existing board view)
        board_tab = QtWidgets.QWidget()
        board_layout = QtWidgets.QVBoxLayout(board_tab)
        board_layout.setContentsMargins(0, 0, 0, 0)

        # Board scroll area with better styling
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Custom scrollbar styling for better visibility
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {SURFACE_BG};
                border: none;
            }}
            QScrollBar:horizontal {{
                background: {ELEVATED_BG};
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {ACCENT};
                border-radius: 6px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(56, 189, 248, 0.8);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)

        # Board container
        self.board_container = QtWidgets.QWidget()
        self.board_layout = QtWidgets.QHBoxLayout(self.board_container)
        self.board_layout.setContentsMargins(16, 16, 16, 16)
        self.board_layout.setSpacing(12)
        self.board_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.board_container)
        board_layout.addWidget(self.scroll)
        
        # Placeholder for login state
        self.empty_state = QtWidgets.QLabel()
        self.empty_state.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet(
            "color: #94A3B8; font-size: 14px; padding: 60px;"
        )
        self.empty_state.hide()
        board_layout.addWidget(self.empty_state)

        # My Tasks tab
        self.my_tasks_widget = self._create_my_tasks_view()

        # Reports tab
        self.reports_widget = self._create_reports_view()

        # Add tabs
        self.tab_widget.addTab(board_tab, "📋 Board")
        self.tab_widget.addTab(self.my_tasks_widget, "👤 My Tasks")
        self.tab_widget.addTab(self.reports_widget, "📊 Reports")

        # Connect tab change to refresh data
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tab_widget, 1)

        self._update_authenticated_controls(enabled=False)

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------

    def _attempt_initial_login(self) -> None:
        if not self.db:
            return

        token = get_remembered_kanban_session_token()
        auth: Optional[AuthResult] = None
        if token:
            auth = resume_session(token, db_manager=self.db)

        if not auth:
            auth = self._prompt_login(allow_cancel=False)

        if auth:
            self._apply_auth_result(auth)
        else:
            self._show_logged_out_state("Login is required to view the Kanban board.")

    def _ensure_authenticated(self) -> bool:
        if self.auth_result and self.manager:
            return True

        auth = self._prompt_login(allow_cancel=True)
        if not auth:
            self._show_logged_out_state("Login cancelled. Use the account menu to sign in.")
            return False

        self._apply_auth_result(auth)
        return True

    def _prompt_login(self, allow_cancel: bool) -> Optional[AuthResult]:
        if not self.db:
            return None

        remembered_username = None
        if self.auth_result and self.auth_result.user:
            remembered_username = self.auth_result.user.username
        dialog = LoginDialog(self.db, self, remembered_username=remembered_username, allow_cancel=allow_cancel)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.auth_result
        return None

    def _apply_auth_result(self, auth: AuthResult) -> None:
        self.auth_result = auth
        remember_token = auth.session.session_token if auth.remember_me else None
        set_remembered_kanban_session_token(remember_token)

        self.manager = KanbanManager(
            self.db,
            current_user_id=auth.user.id,
            session_token=auth.session.session_token,
        )

        self._update_authenticated_controls(enabled=True, username=auth.user.display_name)
        self._clear_board()
        self._load_board()
        
        # Start auto-refresh timer
        self.auto_refresh_timer.start()

        if auth.must_change_password:
            QtWidgets.QMessageBox.information(
                self,
                "Password Change Required",
                "You must change your password now.",
            )
            self._change_password()

    def _show_logged_out_state(self, message: str) -> None:
        self.auth_result = None
        self.manager = None
        self._update_authenticated_controls(enabled=False)
        self._clear_board()
        self.empty_state.setText(message)
        self.empty_state.show()

    def _switch_user(self) -> None:
        self._sign_out()
        auth = self._prompt_login(allow_cancel=True)
        if auth:
            self._apply_auth_result(auth)
        else:
            self._show_logged_out_state("Switch user cancelled. Use the account menu to sign in.")

    def _sign_out(self) -> None:
        if self.auth_result:
            logout(self.auth_result.session.session_token, db_manager=self.db)
        set_remembered_kanban_session_token(None)
        self.auth_result = None
        self.manager = None
        
        # Stop auto-refresh timer
        self.auto_refresh_timer.stop()
        
        self._update_authenticated_controls(enabled=False)
        self._clear_board()
        self.empty_state.setText("Signed out. Use the account menu to sign in.")
        self.empty_state.show()

    def _change_password(self) -> None:
        if not self.auth_result:
            return
        dialog = ChangePasswordDialog(self.auth_result.user, self.db, parent=self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            QtWidgets.QMessageBox.information(self, "Password Updated", "Password updated successfully.")

    def _open_admin_reset(self) -> None:
        if not self.auth_result:
            return
        dialog = AdminPasswordResetDialog(self.auth_result.user, self.db, parent=self)
        dialog.exec()

    def _clear_board(self) -> None:
        # remove existing column widgets
        while self.board_layout.count():
            item = self.board_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.columns = []
        self.column_widgets = {}

    def _update_authenticated_controls(self, *, enabled: bool, username: str | None = None) -> None:
        for widget in [self.search_input, self.assignee_filter, self.priority_filter, self.refresh_btn, self.manage_groups_btn, self.new_task_btn]:
            widget.setEnabled(enabled)
        if self.account_button:
            self.account_button.setEnabled(True)  # allow menu to open for login actions
            display = username or "Not signed in"
            self.account_button.setText(display)
        if self.admin_reset_action:
            is_admin = bool(self.auth_result and self.auth_result.user.role in {"admin", "manager"})
            self.admin_reset_action.setVisible(enabled and is_admin)
        if self.change_password_action:
            self.change_password_action.setEnabled(enabled)
        if self.switch_user_action:
            self.switch_user_action.setEnabled(True)
        if self.sign_out_action:
            self.sign_out_action.setEnabled(enabled)

    # ------------------------------------------------------------------

    def _create_toolbar(self) -> QtWidgets.QWidget:
        """Create the toolbar with filters and actions."""
        toolbar_container = QtWidgets.QWidget()
        toolbar_main_layout = QtWidgets.QVBoxLayout(toolbar_container)
        toolbar_main_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_main_layout.setSpacing(0)
        
        # Main toolbar (always visible)
        toolbar = QtWidgets.QFrame()
        toolbar.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_BG};
                border-bottom: 1px solid rgba(56, 189, 248, 0.2);
            }}
            """
        )

        layout = QtWidgets.QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Title
        title_container = QtWidgets.QHBoxLayout()
        
        icon_label = QtWidgets.QLabel("📋")
        icon_label.setStyleSheet(f"font-size: 16px; background-color: {CARD_BG}; border: none;")
        title_container.addWidget(icon_label)
        title = QtWidgets.QLabel("Kanban Board")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT_PRIMARY}; background-color: {CARD_BG}; border: none;")
        title_container.addWidget(title)
        title_container.addStretch()
        title_wrapper = QtWidgets.QWidget()
        title_wrapper.setStyleSheet(f"background-color: {CARD_BG};")
        title_wrapper.setLayout(title_container)
        layout.addWidget(title_wrapper)

        # Filters container
        self.filters_container = QtWidgets.QWidget()
        self.filters_container.setStyleSheet(f"background-color: {CARD_BG};")
        filters_layout = QtWidgets.QHBoxLayout(self.filters_container)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)
        
        # Search box
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedWidth(200)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
            """
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        filters_layout.addWidget(self.search_input)

        # Filter by assignee
        self.assignee_filter = QtWidgets.QComboBox()
        self.assignee_filter.setFixedWidth(150)
        self.assignee_filter.addItem("👤 All Users", None)
        self.assignee_filter.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ELEVATED_BG};
                border: 1px solid {ACCENT};
                selection-background-color: {ACCENT};
                selection-color: #051221;
            }}
            """
        )
        self.assignee_filter.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.assignee_filter)

        # Filter by priority
        self.priority_filter = QtWidgets.QComboBox()
        self.priority_filter.setFixedWidth(140)
        self.priority_filter.addItem("🎯 All Priorities", None)
        self.priority_filter.addItem("🔴 Critical", "critical")
        self.priority_filter.addItem("🟠 High", "high")
        self.priority_filter.addItem("🟡 Medium", "medium")
        self.priority_filter.addItem("🟢 Low", "low")
        self.priority_filter.setStyleSheet(self.assignee_filter.styleSheet())
        self.priority_filter.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.priority_filter)
        
        layout.addWidget(self.filters_container)
        
        layout.addStretch()

        # Account button
        self.account_button = QtWidgets.QToolButton()
        self.account_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.account_button.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600; padding: 4px 8px;"
        )
        self.account_menu = QtWidgets.QMenu(self.account_button)
        self.account_button.setMenu(self.account_menu)

        self.switch_user_action = self.account_menu.addAction("Switch User", self._switch_user)
        self.change_password_action = self.account_menu.addAction("Change Password", self._change_password)
        self.admin_reset_action = self.account_menu.addAction("Reset Another User Password", self._open_admin_reset)
        self.account_menu.addSeparator()
        self.sign_out_action = self.account_menu.addAction("Sign Out", self._sign_out)
        self.account_button.setEnabled(False)

        layout.addWidget(self.account_button)

        # Refresh button
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 189, 248, 0.2);
                border-color: {ACCENT};
            }}
            """
        )
        self.refresh_btn.clicked.connect(self._refresh_board)
        layout.addWidget(self.refresh_btn)

        # Manage Groups button
        self.manage_groups_btn = QtWidgets.QPushButton("👥 Manage Groups")
        self.manage_groups_btn.setFixedHeight(36)
        self.manage_groups_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 189, 248, 0.2);
                border-color: {ACCENT};
            }}
            """
        )
        self.manage_groups_btn.clicked.connect(self._manage_groups)
        layout.addWidget(self.manage_groups_btn)

        # New Task button
        self.new_task_btn = QtWidgets.QPushButton("➕ New Task")
        self.new_task_btn.setFixedHeight(36)
        self.new_task_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: #051221;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 189, 248, 0.9);
            }}
            """
        )
        self.new_task_btn.clicked.connect(self._create_new_task)
        layout.addWidget(self.new_task_btn)

        toolbar_main_layout.addWidget(toolbar)
        return toolbar_container
    
    def _create_my_tasks_view(self) -> QtWidgets.QWidget:
        """Create the My Tasks view widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QtWidgets.QLabel("My Tasks")
        header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        layout.addWidget(header)

        # Filter tabs
        filter_tabs = QtWidgets.QTabWidget()
        filter_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {ELEVATED_BG}; border-radius: 6px; }}
            QTabBar::tab {{ padding: 8px 16px; background: {ELEVATED_BG}; color: {TEXT_MUTED}; }}
            QTabBar::tab:selected {{ background: {ACCENT}; color: {TEXT_PRIMARY}; }}
        """)

        # Create task lists
        self.my_assigned_list = QtWidgets.QListWidget()
        self.my_created_list = QtWidgets.QListWidget()
        self.my_overdue_list = QtWidgets.QListWidget()

        for lst in [self.my_assigned_list, self.my_created_list, self.my_overdue_list]:
            lst.setStyleSheet(f"""
                QListWidget {{
                    background: {CARD_BG};
                    border: none;
                    border-radius: 6px;
                    padding: 8px;
                }}
                QListWidget::item {{
                    background: {ELEVATED_BG};
                    border-radius: 6px;
                    padding: 12px;
                    margin: 4px;
                    color: {TEXT_PRIMARY};
                }}
                QListWidget::item:hover {{
                    background: {SURFACE_BG};
                }}
                QListWidget::item:selected {{
                    background: {ACCENT};
                }}
            """)
            lst.itemDoubleClicked.connect(self._on_my_task_clicked)

        filter_tabs.addTab(self.my_assigned_list, "📌 Assigned to Me")
        filter_tabs.addTab(self.my_created_list, "✏️ Created by Me")
        filter_tabs.addTab(self.my_overdue_list, "⚠️ Overdue")

        layout.addWidget(filter_tabs, 1)

        return widget

    def _create_reports_view(self) -> QtWidgets.QWidget:
        """Create the Reports view widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QtWidgets.QLabel("Task Reports & Statistics")
        header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        layout.addWidget(header)

        # Stats cards container
        stats_container = QtWidgets.QWidget()
        stats_layout = QtWidgets.QGridLayout(stats_container)
        stats_layout.setSpacing(16)

        # Create stat cards
        self.total_tasks_card = self._create_stat_card("Total Tasks", "0", ACCENT)
        self.completed_tasks_card = self._create_stat_card("Completed", "0", SUCCESS)
        self.in_progress_card = self._create_stat_card("In Progress", "0", INFO)
        self.overdue_card = self._create_stat_card("Overdue", "0", WARNING)

        stats_layout.addWidget(self.total_tasks_card, 0, 0)
        stats_layout.addWidget(self.completed_tasks_card, 0, 1)
        stats_layout.addWidget(self.in_progress_card, 0, 2)
        stats_layout.addWidget(self.overdue_card, 0, 3)

        layout.addWidget(stats_container)

        # Tasks by category
        category_header = QtWidgets.QLabel("Tasks by Category")
        category_header.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 20px;")
        layout.addWidget(category_header)

        self.category_list = QtWidgets.QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background: {CARD_BG};
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QListWidget::item {{
                background: {ELEVATED_BG};
                border-radius: 6px;
                padding: 12px;
                margin: 4px;
                color: {TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.category_list)

        # Tasks by user
        user_header = QtWidgets.QLabel("Tasks by Assignee")
        user_header.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 20px;")
        layout.addWidget(user_header)

        self.user_list = QtWidgets.QListWidget()
        self.user_list.setStyleSheet(f"""
            QListWidget {{
                background: {CARD_BG};
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QListWidget::item {{
                background: {ELEVATED_BG};
                border-radius: 6px;
                padding: 12px;
                margin: 4px;
                color: {TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.user_list)

        layout.addStretch()

        return widget

    def _create_stat_card(self, title: str, value: str, color: str) -> QtWidgets.QFrame:
        """Create a statistics card widget."""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-weight: 600;")
        layout.addWidget(title_label)

        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName(f"{title}_value")
        value_label.setStyleSheet(f"font-size: 32px; color: {color}; font-weight: 700;")
        layout.addWidget(value_label)

        return card

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change to refresh data."""
        if not self.manager or not self.auth_result:
            return

        if index == 1:  # My Tasks tab
            self._refresh_my_tasks()
        elif index == 2:  # Reports tab
            self._refresh_reports()

    def _refresh_my_tasks(self) -> None:
        """Refresh the My Tasks view."""
        if not self.manager or not self.auth_result:
            return

        try:
            user_id = self.auth_result.user.id

            # Assigned to me
            assigned_tasks = self.manager.get_tasks_by_assignee(user_id)
            self.my_assigned_list.clear()
            for task in assigned_tasks:
                if not task.is_deleted and task.status != "Done":
                    item_text = f"{task.task_number} - {task.title} [{task.status}]"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_assigned_list.addItem(item)

            if self.my_assigned_list.count() == 0:
                item = QtWidgets.QListWidgetItem("No tasks assigned to you")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                self.my_assigned_list.addItem(item)

            # Created by me
            all_tasks = self.manager.get_all_tasks()
            self.my_created_list.clear()
            created_count = 0
            for task in all_tasks:
                if task.created_by == user_id and not task.is_deleted:
                    item_text = f"{task.task_number} - {task.title} [{task.status}]"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_created_list.addItem(item)
                    created_count += 1

            if created_count == 0:
                item = QtWidgets.QListWidgetItem("No tasks created by you")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                self.my_created_list.addItem(item)

            # Overdue tasks
            from datetime import datetime, date
            self.my_overdue_list.clear()
            overdue_count = 0
            today = datetime.now().date()
            for task in all_tasks:
                # Convert deadline to date for comparison
                deadline_date = task.deadline.date() if isinstance(task.deadline, datetime) else task.deadline if isinstance(task.deadline, date) else None
                if (task.assigned_to == user_id and 
                    deadline_date and 
                    deadline_date < today and 
                    task.status != "Done" and 
                    not task.is_deleted):
                    deadline_str = deadline_date.strftime('%Y-%m-%d') if deadline_date else "N/A"
                    item_text = f"{task.task_number} - {task.title} [Due: {deadline_str}]"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_overdue_list.addItem(item)
                    overdue_count += 1

            if overdue_count == 0:
                item = QtWidgets.QListWidgetItem("No overdue tasks")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                self.my_overdue_list.addItem(item)

        except Exception as e:
            print(f"Error refreshing my tasks: {e}")

    def _on_my_task_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """Handle click on a task in My Tasks view."""
        task_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if task_id:
            self._show_task_detail(task_id)

    def _refresh_reports(self) -> None:
        """Refresh the Reports view with current statistics."""
        if not self.manager:
            return

        try:
            # Get statistics
            stats = self.manager.get_statistics()

            # Update stat cards
            total_card = self.total_tasks_card.findChild(QtWidgets.QLabel, "Total Tasks_value")
            if total_card:
                total_card.setText(str(stats.get("total_tasks", 0)))

            completed_card = self.completed_tasks_card.findChild(QtWidgets.QLabel, "Completed_value")
            if completed_card:
                completed_card.setText(str(stats.get("completed_tasks", 0)))

            in_progress_card = self.in_progress_card.findChild(QtWidgets.QLabel, "In Progress_value")
            if in_progress_card:
                in_progress = len([t for t in self.manager.get_all_tasks() if t.status == "In Progress" and not t.is_deleted])
                in_progress_card.setText(str(in_progress))

            overdue_card = self.overdue_card.findChild(QtWidgets.QLabel, "Overdue_value")
            if overdue_card:
                overdue_card.setText(str(stats.get("overdue_tasks", 0)))

            # Tasks by category
            self.category_list.clear()
            tasks = self.manager.get_all_tasks()
            category_counts = {}
            for task in tasks:
                if not task.is_deleted:
                    cat = task.category or "Uncategorized"
                    category_counts[cat] = category_counts.get(cat, 0) + 1

            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                self.category_list.addItem(f"{category}: {count} tasks")

            # Tasks by assignee
            self.user_list.clear()
            user_counts = {}
            users = self.manager.get_all_users()
            user_map = {u.id: u.display_name for u in users}

            for task in tasks:
                if not task.is_deleted:
                    if task.assigned_to:
                        user_name = user_map.get(task.assigned_to, "Unknown")
                        user_counts[user_name] = user_counts.get(user_name, 0) + 1
                    else:
                        user_counts["Unassigned"] = user_counts.get("Unassigned", 0) + 1

            for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
                self.user_list.addItem(f"{user}: {count} tasks")

        except Exception as e:
            print(f"Error refreshing reports: {e}")

    def _load_board(self) -> None:
        """Load columns and tasks from database."""
        if not self.manager:
            return

        try:
            self.empty_state.hide()
            # Get all columns
            self.columns = self.manager.get_all_columns()

            # Populate assignee filter
            users = self.manager.get_all_users()
            self.assignee_filter.clear()
            self.assignee_filter.addItem("👤 All Users", None)
            for user in users:
                self.assignee_filter.addItem(f"👤 {user.display_name}", user.id)

            # Create column widgets
            for column in self.columns:
                column_widget = self._create_column_widget(column)
                self.column_widgets[column.id] = column_widget
                self.board_layout.addWidget(column_widget)

            # Load tasks into columns
            self._refresh_tasks()

        except Exception as e:
            self._show_error(f"Failed to load board: {e}")

    def _create_column_widget(self, column) -> QtWidgets.QWidget:
        """Create a column widget."""
        column_container = DropZoneColumn(column.id)
        column_container.setMinimumWidth(240)
        column_container.setMaximumWidth(320)
        column_container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        column_container.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 12px;
            }}
            """
        )
        
        # Connect drop signal
        column_container.task_dropped.connect(self._on_task_dropped)

        layout = QtWidgets.QVBoxLayout(column_container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Column header
        header = QtWidgets.QHBoxLayout()

        color_dot = QtWidgets.QLabel("●")
        color_dot.setStyleSheet(f"color: {column.color}; font-size: 14px; border: none;")
        header.addWidget(color_dot)

        name_label = QtWidgets.QLabel(column.name)
        name_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY}; border: none;")
        header.addWidget(name_label)

        header.addStretch()

        # Task count badge
        count_badge = QtWidgets.QLabel("0")
        count_badge.setObjectName(f"count_badge_{column.id}")
        count_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgba(56, 189, 248, 0.15);
                color: {ACCENT};
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )
        header.addWidget(count_badge)

        layout.addLayout(header)

        # WIP limit warning
        if column.wip_limit:
            wip_label = QtWidgets.QLabel(f"WIP Limit: {column.wip_limit}")
            wip_label.setObjectName(f"wip_label_{column.id}")
            wip_label.setStyleSheet(
                f"font-size: 10px; color: {TEXT_MUTED}; font-weight: 600; border: none; padding: 2px 0;"
            )
            layout.addWidget(wip_label)

        # Tasks scroll area
        tasks_scroll = QtWidgets.QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        tasks_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tasks_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        tasks_container = QtWidgets.QWidget()
        tasks_container.setObjectName(f"tasks_container_{column.id}")
        tasks_layout = QtWidgets.QVBoxLayout(tasks_container)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_layout.setSpacing(8)
        tasks_layout.addStretch()

        tasks_scroll.setWidget(tasks_container)
        layout.addWidget(tasks_scroll, 1)

        return column_container

    def _auto_refresh(self) -> None:
        """Auto-refresh the board silently in background."""
        if not self.manager or not self.auth_result:
            return
        
        # Only auto-refresh the current tab
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # Board tab
            self._refresh_tasks()
        elif current_tab == 1:  # My Tasks tab
            self._refresh_my_tasks()
        elif current_tab == 2:  # Reports tab
            self._refresh_reports()

    def _refresh_tasks(self) -> None:
        """Refresh tasks in all columns."""
        if not self.manager:
            return

        for column in self.columns:
            # Get column's tasks container
            column_widget = self.column_widgets.get(column.id)
            if not column_widget:
                continue

            tasks_container = column_widget.findChild(QtWidgets.QWidget, f"tasks_container_{column.id}")
            if not tasks_container:
                continue

            # Clear existing tasks
            layout = tasks_container.layout()
            while layout.count() > 1:  # Keep the stretch at the end
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # Get tasks for this column
            tasks = self.manager.get_tasks_by_column(column.id)

            # Apply filters
            tasks = self._filter_tasks(tasks)

            # Add task cards
            for task in tasks:
                task_card = self._create_task_card(task)
                layout.insertWidget(layout.count() - 1, task_card)

            # Update task count
            count_badge = column_widget.findChild(QtWidgets.QLabel, f"count_badge_{column.id}")
            if count_badge:
                count_badge.setText(str(len(tasks)))

            # WIP limit warning
            if column.wip_limit and len(tasks) > column.wip_limit:
                wip_label = column_widget.findChild(QtWidgets.QLabel, f"wip_label_{column.id}")
                if wip_label:
                    wip_label.setStyleSheet(
                        f"font-size: 10px; color: {WARNING}; font-weight: 700; border: none; padding: 2px 0;"
                    )
                    wip_label.setText(f"⚠️ WIP Limit Exceeded: {len(tasks)}/{column.wip_limit}")

    def _filter_tasks(self, tasks: list) -> list:
        """Apply current filters to task list."""
        filtered = tasks

        # Assignee filter
        assignee_id = self.assignee_filter.currentData()
        if assignee_id is not None:
            filtered = [t for t in filtered if t.assigned_to == assignee_id]

        # Priority filter
        priority = self.priority_filter.currentData()
        if priority is not None:
            filtered = [t for t in filtered if t.priority == priority]

        # Search filter
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered = [
                t
                for t in filtered
                if search_text in t.title.lower() or (t.description and search_text in t.description.lower())
            ]

        return filtered

    def _create_task_card(self, task) -> QtWidgets.QWidget:
        """Create a task card widget."""
        card = DraggableTaskCard(task)
        card.clicked.connect(self._show_task_detail)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Task number and priority
        header = QtWidgets.QHBoxLayout()

        task_num = QtWidgets.QLabel(task.task_number)
        task_num.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; border: none;")
        header.addWidget(task_num)

        header.addStretch()

        # Priority badge
        priority_colors = {
            "critical": "#EF4444",
            "high": "#F59E0B",
            "medium": "#3B82F6",
            "low": "#10B981",
        }
        priority_badge = QtWidgets.QLabel(task.priority.upper())
        priority_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgba({int(priority_colors.get(task.priority, '#3B82F6')[1:3], 16)}, 
                                        {int(priority_colors.get(task.priority, '#3B82F6')[3:5], 16)}, 
                                        {int(priority_colors.get(task.priority, '#3B82F6')[5:7], 16)}, 0.15);
                color: {priority_colors.get(task.priority, '#3B82F6')};
                border: 1px solid {priority_colors.get(task.priority, '#3B82F6')};
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 700;
            }}
            """
        )
        header.addWidget(priority_badge)

        layout.addLayout(header)

        # Task title
        title = QtWidgets.QLabel(task.title)
        title.setWordWrap(True)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; border: none;")
        layout.addWidget(title)

        # Task description preview (if available)
        if task.description and task.description.strip():
            description_text = task.description.strip()
            # Truncate to 80 characters for preview
            if len(description_text) > 80:
                description_preview = description_text[:80] + "..."
            else:
                description_preview = description_text
            
            description_label = QtWidgets.QLabel(description_preview)
            description_label.setWordWrap(True)
            description_label.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 11px; border: none; padding-top: 4px; line-height: 1.4;"
            )
            # Set tooltip with full description
            description_label.setToolTip(description_text)
            layout.addWidget(description_label)

        # Task metadata
        meta = QtWidgets.QHBoxLayout()

        # Status badge (show for special statuses)
        if task.status == "blocked":
            status_badge = QtWidgets.QLabel("🚫 BLOCKED")
            status_badge.setStyleSheet(
                "color: #EF4444; font-size: 9px; font-weight: 700; "
                "background: rgba(239, 68, 68, 0.15); padding: 2px 4px; "
                "border-radius: 3px; border: none;"
            )
            meta.addWidget(status_badge)
        elif task.status == "archived":
            status_badge = QtWidgets.QLabel("📦 ARCHIVED")
            status_badge.setStyleSheet(
                "color: #94A3B8; font-size: 9px; font-weight: 700; "
                "background: rgba(148, 163, 184, 0.15); padding: 2px 4px; "
                "border-radius: 3px; border: none;"
            )
            meta.addWidget(status_badge)
        elif task.was_completed_late:
            status_badge = QtWidgets.QLabel("⏰ LATE")
            status_badge.setStyleSheet(
                "color: #F59E0B; font-size: 9px; font-weight: 700; "
                "background: rgba(245, 158, 11, 0.15); padding: 2px 4px; "
                "border-radius: 3px; border: none;"
            )
            meta.addWidget(status_badge)

        # Show assignee (user or group)
        try:
            if task.assigned_group:
                # Task assigned to group
                group = task.assigned_group
                group_label = QtWidgets.QLabel(f"👥 {group.name} ({group.member_count})")
                group_label.setStyleSheet(
                    f"color: {TEXT_MUTED}; font-size: 10px; border: none; "
                    f"background: rgba({int(group.color[1:3], 16)}, {int(group.color[3:5], 16)}, {int(group.color[5:7], 16)}, 0.2); "
                    f"padding: 2px 4px; border-radius: 3px;"
                )
                
                # Add tooltip showing group members
                if self.manager:
                    try:
                        members = self.manager.get_group_members(group.id)
                        member_names = [m.display_name for m in members[:5]]  # Show first 5 members
                        if len(members) > 5:
                            member_names.append(f"... and {len(members) - 5} more")
                        tooltip = f"Group: {group.name}\n\nMembers:\n" + "\n".join([f"• {name}" for name in member_names])
                        group_label.setToolTip(tooltip)
                    except:
                        pass
                
                meta.addWidget(group_label)
            elif task.assignee:
                # Task assigned to individual user
                assignee_label = QtWidgets.QLabel(f"👤 {task.assignee.display_name}")
                assignee_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none;")
                meta.addWidget(assignee_label)
        except Exception as e:
            # If there's an issue loading assignee/group, just skip it
            print(f"Warning: Could not load assignee info: {e}")

        if task.deadline:
            deadline_label = QtWidgets.QLabel(f"📅 {task.deadline.strftime('%m/%d')}")
            if task.is_overdue:
                deadline_label.setStyleSheet(f"color: #EF4444; font-size: 10px; font-weight: 700; border: none;")
            else:
                deadline_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none;")
            meta.addWidget(deadline_label)

        if task.comment_count > 0:
            comment_label = QtWidgets.QLabel(f"💬 {task.comment_count}")
            comment_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none;")
            meta.addWidget(comment_label)

        if task.attachment_count > 0:
            attachment_label = QtWidgets.QLabel(f"📎 {task.attachment_count}")
            attachment_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none;")
            meta.addWidget(attachment_label)

        meta.addStretch()
        layout.addLayout(meta)

        return card

    def _on_task_dropped(self, task_id: int, column_id: int) -> None:
        """Handle task drop on column."""
        if not self.manager:
            return
            
        try:
            print(f"[DragDrop] Drop detected for task {task_id} -> column {column_id}")
            # Check if task exists and get its current column
            task = self.manager.get_task(task_id)
            if not task:
                print(f"[DragDrop] Task {task_id} not found during drop")
                return
            
            old_column_id = task.column_id
            print(f"[DragDrop] Task {task_id} currently in column {old_column_id}")
            
            # Check if already in this column
            if old_column_id == column_id:
                print(f"[DragDrop] Task {task_id} already in column {column_id}, ignoring drop")
                return  # No need to move
            
            # Don't hold onto the task object - it will be detached after this
            del task
            
            # Move task to new column (use column_id directly)
            print(f"[DragDrop] Moving task {task_id} to column {column_id}")
            self.manager.move_task(task_id, column_id)
            
            # Verify new column value
            updated_task = self.manager.get_task(task_id)
            if updated_task:
                print(f"[DragDrop] Task {task_id} reported column {updated_task.column_id} after move")
            else:
                print(f"[DragDrop] Task {task_id} could not be reloaded after move")
            
            # Refresh board - this will get fresh task objects with proper sessions
            print(f"[DragDrop] Refreshing tasks after move")
            self._refresh_tasks()
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Drag and drop error: {error_details}")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to move task: {str(e)}"
            )

    def _refresh_board(self) -> None:
        """Refresh the entire board."""
        if not self._ensure_authenticated():
            return
        self._refresh_tasks()
        if self.auth_result:
            update_last_activity(self.auth_result.session.session_token, db_manager=self.db)
        QtWidgets.QMessageBox.information(self, "Board Refreshed", "The Kanban board has been refreshed successfully.")

    def _on_search_changed(self) -> None:
        """Handle search text changes."""
        self._refresh_tasks()

    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        self._refresh_tasks()

    def _create_new_task(self) -> None:
        """Open dialog to create a new task."""
        from kanban.ui_components import NewTaskDialog

        dialog = NewTaskDialog(self.manager, parent=self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._refresh_board()

    def _manage_groups(self) -> None:
        """Open group management dialog."""
        from kanban.ui_components import GroupManagementDialog

        dialog = GroupManagementDialog(self.manager, parent=self)
        dialog.exec()
        # Refresh board in case group assignments changed
        self._refresh_tasks()

    def _show_task_detail(self, task_id: int) -> None:
        """Open task detail dialog."""
        from kanban.ui_components import TaskDetailDialog
        
        dialog = TaskDetailDialog(task_id, self.manager, parent=self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._refresh_tasks()

    def _open_task_detail(self, task_id: int) -> None:
        """Alias for _show_task_detail."""
        self._show_task_detail(task_id)

    def _show_error(self, message: str) -> None:
        """Show error message."""
        error_label = QtWidgets.QLabel(f"❌ {message}")
        error_label.setStyleSheet(
            f"""
            QLabel {{
                color: #EF4444;
                font-size: 16px;
                font-weight: 600;
                padding: 40px;
            }}
            """
        )
        error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.board_layout.addWidget(error_label)


def build_kanban_section(parent: QtWidgets.QWidget) -> None:
    """
    Build the Kanban section UI.

    Args:
        parent: Parent widget to add the Kanban board to
    """
    layout = QtWidgets.QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)

    board = KanbanBoardWidget(parent)
    layout.addWidget(board)


