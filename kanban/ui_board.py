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

# UI Labels (configurable)
UNASSIGNED_LABEL = "Unassigned"


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
        self.column_page_sizes = {}  # Track how many tasks to show per column
        self.column_view_modes = {}  # Track view mode per column (auto, detailed, compact, mini)
        self.account_button: QtWidgets.QToolButton | None = None
        self.account_menu: QtWidgets.QMenu | None = None
        self.admin_reset_action: QtGui.QAction | None = None
        self.change_password_action: QtGui.QAction | None = None
        self.switch_user_action: QtGui.QAction | None = None
        self.sign_out_action: QtGui.QAction | None = None
        self._last_username: str | None = None
        
        # Pagination settings
        self.TASKS_PER_PAGE = 20
        
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
        # Reports tab added conditionally after authentication (only for admin/manager)

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
        self._update_reports_tab_visibility()
        self._clear_board()
        self._load_board()
        
        # Refresh My Tasks and Reports on login
        self._refresh_my_tasks()
        if auth.user.role in {'admin', 'manager'}:
            self._refresh_reports()
        
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
        self._update_reports_tab_visibility()
        self._clear_board()
        self._clear_my_tasks()
        self._clear_reports()
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
        self._clear_my_tasks()  # Clear My Tasks data
        self._clear_reports()   # Clear Reports data
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

    def _clear_my_tasks(self) -> None:
        """Clear all My Tasks lists."""
        if hasattr(self, 'my_assigned_list'):
            self.my_assigned_list.clear()
            # Force clear all items
            while self.my_assigned_list.count() > 0:
                self.my_assigned_list.takeItem(0)
        
        if hasattr(self, 'my_created_list'):
            self.my_created_list.clear()
            # Force clear all items
            while self.my_created_list.count() > 0:
                self.my_created_list.takeItem(0)
        
        if hasattr(self, 'my_overdue_list'):
            self.my_overdue_list.clear()
            # Force clear all items
            while self.my_overdue_list.count() > 0:
                self.my_overdue_list.takeItem(0)
        
        # Clear summary widget
        if hasattr(self, 'summary_total'):
            self.summary_total.setText("Total: 0")
            self.summary_done.setText("✅ Done: 0")
            self.summary_active.setText("⚡ Active: 0")
            self.summary_overdue.setText("⚠️ Overdue: 0")

    def _clear_reports(self) -> None:
        """Clear all Reports data."""
        if hasattr(self, 'performance_table'):
            self.performance_table.setRowCount(0)
        
        # Clear stat cards
        if hasattr(self, 'total_tasks_card'):
            total_value = self.total_tasks_card.findChild(QtWidgets.QLabel, "Total_value")
            if total_value:
                total_value.setText("0")
        
        if hasattr(self, 'completed_tasks_card'):
            completed_value = self.completed_tasks_card.findChild(QtWidgets.QLabel, "Done_value")
            completed_subtitle = self.completed_tasks_card.findChild(QtWidgets.QLabel, "Done_subtitle")
            if completed_value:
                completed_value.setText("0")
            if completed_subtitle:
                completed_subtitle.setText("0%")
        
        if hasattr(self, 'in_progress_card'):
            in_progress_value = self.in_progress_card.findChild(QtWidgets.QLabel, "In Progress_value")
            if in_progress_value:
                in_progress_value.setText("0")
        
        if hasattr(self, 'overdue_card'):
            overdue_value = self.overdue_card.findChild(QtWidgets.QLabel, "Overdue_value")
            if overdue_value:
                overdue_value.setText("0")

    def _update_authenticated_controls(self, *, enabled: bool, username: str | None = None) -> None:
        for widget in [self.search_input, self.assignee_filter, self.group_filter, self.priority_filter, self.refresh_btn, self.manage_groups_btn, self.new_task_btn]:
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

    def _update_reports_tab_visibility(self) -> None:
        """Show or hide Reports tab based on user role (admin/manager only)."""
        if not self.auth_result:
            # Remove reports tab if not authenticated
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "📊 Reports":
                    self.tab_widget.removeTab(i)
                    break
            return
        
        is_manager_or_admin = self.auth_result.user.role in {"admin", "manager"}
        
        # Check if Reports tab already exists
        reports_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "📊 Reports":
                reports_tab_index = i
                break
        
        if is_manager_or_admin and reports_tab_index == -1:
            # Add Reports tab (after My Tasks)
            self.tab_widget.addTab(self.reports_widget, "📊 Reports")
        elif not is_manager_or_admin and reports_tab_index != -1:
            # Remove Reports tab
            self.tab_widget.removeTab(reports_tab_index)

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
        
        # Search box with clear button
        search_container = QtWidgets.QWidget()
        search_layout = QtWidgets.QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search...")
        self.search_input.setFixedWidth(180)
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
        search_layout.addWidget(self.search_input)
        
        # Clear search button
        clear_search_btn = QtWidgets.QPushButton("✕")
        clear_search_btn.setFixedSize(24, 24)
        clear_search_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {SURFACE_BG};
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 4px;
                color: {TEXT_MUTED};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ELEVATED_BG};
                border-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
            """
        )
        clear_search_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_search_btn)
        
        # Search results label
        self.search_results_label = QtWidgets.QLabel("")
        self.search_results_label.setStyleSheet(f"color: {SUCCESS}; font-size: 11px; font-weight: 600;")
        self.search_results_label.setVisible(False)
        search_layout.addWidget(self.search_results_label)
        
        filters_layout.addWidget(search_container)

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

        # Filter by group
        self.group_filter = QtWidgets.QComboBox()
        self.group_filter.setFixedWidth(150)
        self.group_filter.addItem("👥 All Groups", None)
        self.group_filter.setStyleSheet(self.assignee_filter.styleSheet())
        self.group_filter.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(self.group_filter)
        
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

        # Header with search
        header_row = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel("My Tasks")
        header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        header_row.addWidget(header)
        header_row.addStretch()
        
        # Search box for My Tasks
        self.my_tasks_search = QtWidgets.QLineEdit()
        self.my_tasks_search.setPlaceholderText("🔍 Search my tasks...")
        self.my_tasks_search.setFixedWidth(250)
        self.my_tasks_search.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
            """
        )
        self.my_tasks_search.textChanged.connect(self._on_my_tasks_filter_changed)
        header_row.addWidget(self.my_tasks_search)
        
        layout.addLayout(header_row)
        
        # Filter bar
        filter_bar = QtWidgets.QWidget()
        filter_bar.setStyleSheet(f"background-color: {ELEVATED_BG}; border-radius: 8px; padding: 12px;")
        filter_layout = QtWidgets.QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        filter_layout.setSpacing(12)
        
        filter_label = QtWidgets.QLabel("Filters:")
        filter_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; font-size: 12px;")
        filter_layout.addWidget(filter_label)
        
        # Status filter
        self.my_tasks_status_filter = QtWidgets.QComboBox()
        self.my_tasks_status_filter.setFixedWidth(140)
        self.my_tasks_status_filter.addItem("All Tasks", None)
        self.my_tasks_status_filter.addItem("Active Only", "active")
        self.my_tasks_status_filter.addItem("Completed", "completed")
        self.my_tasks_status_filter.addItem("In Progress", "in_progress")
        self.my_tasks_status_filter.addItem("In Review", "review")
        self.my_tasks_status_filter.addItem("Blocked", "blocked")
        self.my_tasks_status_filter.setCurrentIndex(1)  # Default to "Active Only"
        self.my_tasks_status_filter.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.1);
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QComboBox:hover {{ border-color: {ACCENT}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {ELEVATED_BG};
                border: 1px solid {ACCENT};
                selection-background-color: {ACCENT};
                selection-color: #051221;
            }}
            """
        )
        self.my_tasks_status_filter.currentIndexChanged.connect(self._on_my_tasks_filter_changed)
        filter_layout.addWidget(self.my_tasks_status_filter)
        
        # Priority filter
        self.my_tasks_priority_filter = QtWidgets.QComboBox()
        self.my_tasks_priority_filter.setFixedWidth(140)
        self.my_tasks_priority_filter.addItem("All Priorities", None)
        self.my_tasks_priority_filter.addItem("🔴 Critical", "critical")
        self.my_tasks_priority_filter.addItem("🟠 High", "high")
        self.my_tasks_priority_filter.addItem("🟡 Medium", "medium")
        self.my_tasks_priority_filter.addItem("🟢 Low", "low")
        self.my_tasks_priority_filter.setStyleSheet(self.my_tasks_status_filter.styleSheet())
        self.my_tasks_priority_filter.currentIndexChanged.connect(self._on_my_tasks_filter_changed)
        filter_layout.addWidget(self.my_tasks_priority_filter)
        
        # Sort by
        self.my_tasks_sort = QtWidgets.QComboBox()
        self.my_tasks_sort.setFixedWidth(180)
        self.my_tasks_sort.addItem("📅 Due Date (Earliest)", "deadline")
        self.my_tasks_sort.addItem("🎯 Priority (Highest)", "priority")
        self.my_tasks_sort.addItem("🔄 Recently Updated", "updated")
        self.my_tasks_sort.addItem("🔢 Task Number", "task_number")
        self.my_tasks_sort.setStyleSheet(self.my_tasks_status_filter.styleSheet())
        self.my_tasks_sort.currentIndexChanged.connect(self._on_my_tasks_filter_changed)
        filter_layout.addWidget(self.my_tasks_sort)
        
        # Clear filters button
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.setFixedWidth(70)
        clear_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {SURFACE_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
                padding: 6px 10px;
                color: {TEXT_MUTED};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ELEVATED_BG};
                border-color: {ACCENT};
                color: {TEXT_PRIMARY};
            }}
            """
        )
        clear_btn.clicked.connect(self._clear_my_tasks_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_bar)
        
        # Status summary widget
        self.my_tasks_summary = QtWidgets.QFrame()
        self.my_tasks_summary.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CARD_BG},
                    stop:1 {ELEVATED_BG});
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 10px;
                padding: 16px;
            }}
            """
        )
        summary_layout = QtWidgets.QHBoxLayout(self.my_tasks_summary)
        summary_layout.setSpacing(20)
        
        self.summary_total = QtWidgets.QLabel("Total: 0")
        self.summary_done = QtWidgets.QLabel("✅ Done: 0")
        self.summary_active = QtWidgets.QLabel("⚡ Active: 0")
        self.summary_overdue = QtWidgets.QLabel("⚠️ Overdue: 0")
        
        for label in [self.summary_total, self.summary_done, self.summary_active, self.summary_overdue]:
            label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 13px;")
            summary_layout.addWidget(label)
        
        summary_layout.addStretch()
        layout.addWidget(self.my_tasks_summary)

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

        # Header with time period selector
        header_row = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel("Task Reports & Statistics")
        header.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        header_row.addWidget(header)
        header_row.addStretch()
        
        # Time period selector for performance metrics
        time_period_label = QtWidgets.QLabel("Time Period:")
        time_period_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 600; font-size: 13px;")
        header_row.addWidget(time_period_label)
        
        self.reports_time_period = QtWidgets.QComboBox()
        self.reports_time_period.setFixedWidth(150)
        self.reports_time_period.addItem("📅 This Month", "month")
        self.reports_time_period.addItem("📅 Last 90 Days", "90days")
        self.reports_time_period.addItem("📅 All Time", "all")
        self.reports_time_period.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
                padding: 6px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox:hover {{ border-color: {ACCENT}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {ELEVATED_BG};
                border: 1px solid {ACCENT};
                selection-background-color: {ACCENT};
                selection-color: #051221;
            }}
            """
        )
        self.reports_time_period.currentIndexChanged.connect(self._on_reports_time_period_changed)
        header_row.addWidget(self.reports_time_period)
        
        layout.addLayout(header_row)

        # Stats cards container (more compact layout)
        stats_container = QtWidgets.QWidget()
        stats_layout = QtWidgets.QHBoxLayout(stats_container)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        # Create stat cards with subtitles (smaller)
        self.total_tasks_card = self._create_compact_stat_card("Total", "0", ACCENT, "All tasks")
        self.completed_tasks_card = self._create_compact_stat_card("Done", "0", SUCCESS, "")
        self.in_progress_card = self._create_compact_stat_card("In Progress", "0", INFO, "Active")
        self.overdue_card = self._create_compact_stat_card("Overdue", "0", WARNING, "Urgent")

        stats_layout.addWidget(self.total_tasks_card)
        stats_layout.addWidget(self.completed_tasks_card)
        stats_layout.addWidget(self.in_progress_card)
        stats_layout.addWidget(self.overdue_card)
        stats_layout.addStretch()

        layout.addWidget(stats_container)

        # Team Performance Metrics
        performance_header = QtWidgets.QLabel("Team Performance Metrics")
        performance_header.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 20px;")
        layout.addWidget(performance_header)
        
        # Performance table
        self.performance_table = QtWidgets.QTableWidget()
        self.performance_table.setColumnCount(6)
        self.performance_table.setHorizontalHeaderLabels([
            "Team Member", "Active", "Done", "On-Time %", "Overdue", "Avg Days"
        ])
        self.performance_table.horizontalHeader().setStretchLastSection(False)
        self.performance_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            self.performance_table.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        self.performance_table.setStyleSheet(f"""
            QTableWidget {{
                background: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                gridline-color: rgba(56, 189, 248, 0.1);
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background: {ELEVATED_BG};
                color: {ACCENT};
                padding: 10px;
                border: none;
                font-weight: 700;
                font-size: 12px;
            }}
            QTableWidget::item:selected {{
                background: rgba(56, 189, 248, 0.3);
            }}
        """)
        self.performance_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.performance_table.setAlternatingRowColors(True)
        layout.addWidget(self.performance_table)

        layout.addStretch()

        return widget

    def _create_stat_card(self, title: str, value: str, color: str, subtitle: str = "") -> QtWidgets.QFrame:
        """Create a statistics card widget with optional subtitle."""
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
        
        # Add subtitle if provided
        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setObjectName(f"{title}_subtitle")
        subtitle_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; font-weight: 500;")
        layout.addWidget(subtitle_label)

        return card

    def _create_compact_stat_card(self, title: str, value: str, color: str, subtitle: str = "") -> QtWidgets.QFrame:
        """Create a compact statistics card for Reports."""
        card = QtWidgets.QFrame()
        card.setFixedWidth(150)
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border-left: 3px solid {color};
                border-radius: 6px;
                padding: 12px;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED}; font-weight: 600;")
        layout.addWidget(title_label)

        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName(f"{title}_value")
        value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: 700;")
        layout.addWidget(value_label)
        
        # Add subtitle if provided
        if subtitle:
            subtitle_label = QtWidgets.QLabel(subtitle)
            subtitle_label.setObjectName(f"{title}_subtitle")
            subtitle_label.setStyleSheet(f"font-size: 9px; color: {TEXT_MUTED}; font-weight: 500;")
            layout.addWidget(subtitle_label)

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
        """Refresh the My Tasks view with filters."""
        if not self.manager or not self.auth_result:
            print("[MyTasks] No manager or auth_result, skipping refresh")
            return

        try:
            from datetime import datetime, date, timedelta
            user_id = self.auth_result.user.id
            today = datetime.now().date()
            
            print(f"[MyTasks] Refreshing for user_id: {user_id}")

            # Get all tasks for this user
            assigned_tasks = self.manager.get_tasks_by_assignee(user_id)
            all_tasks = self.manager.get_all_tasks()
            
            print(f"[MyTasks] Found {len(assigned_tasks)} assigned tasks, {len(all_tasks)} total tasks")
            
            # Calculate summary stats (before filters)
            total_tasks = len([t for t in assigned_tasks if not t.is_deleted])
            done_tasks = len([t for t in assigned_tasks if not t.is_deleted and t.column and t.column.name == "Done"])
            active_tasks = len([t for t in assigned_tasks if not t.is_deleted and t.column and t.column.name != "Done"])
            overdue_tasks = len([t for t in assigned_tasks if not t.is_deleted and t.is_overdue])
            
            # Update summary widget
            self.summary_total.setText(f"Total: {total_tasks}")
            self.summary_done.setText(f"✅ Done: {done_tasks}")
            self.summary_active.setText(f"⚡ Active: {active_tasks}")
            self.summary_overdue.setText(f"⚠️ Overdue: {overdue_tasks}")
            
            # Color code overdue if > 0
            if overdue_tasks > 0:
                self.summary_overdue.setStyleSheet(f"color: {WARNING}; font-weight: 700; font-size: 13px;")
            else:
                self.summary_overdue.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 13px;")

            # Assigned to me (with filters)
            filtered_assigned = [t for t in assigned_tasks if not t.is_deleted]
            filtered_assigned = self._apply_my_tasks_filters(filtered_assigned)
            
            # Clear list completely (remove all items including placeholders)
            self.my_assigned_list.clear()
            while self.my_assigned_list.count() > 0:
                self.my_assigned_list.takeItem(0)
            
            print(f"[MyTasks] Adding {len(filtered_assigned)} tasks to Assigned list")
            
            if filtered_assigned:
                for task in filtered_assigned:
                    column_name = task.column.name if task.column else "Unknown"
                    item_text = f"{task.task_number} - {task.title} [{column_name}]"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_assigned_list.addItem(item)
            else:
                item = QtWidgets.QListWidgetItem("No tasks match filters")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                item.setForeground(QtGui.QColor(TEXT_MUTED))
                self.my_assigned_list.addItem(item)

            # Created by me (with filters)
            created_tasks = [t for t in all_tasks if t.created_by == user_id and not t.is_deleted]
            print(f"[MyTasks] Found {len(created_tasks)} created tasks")
            filtered_created = self._apply_my_tasks_filters(created_tasks)
            
            # Clear list completely (remove all items including placeholders)
            self.my_created_list.clear()
            while self.my_created_list.count() > 0:
                self.my_created_list.takeItem(0)
            
            print(f"[MyTasks] Adding {len(filtered_created)} tasks to Created list")
            
            if filtered_created:
                for task in filtered_created:
                    column_name = task.column.name if task.column else "Unknown"
                    item_text = f"{task.task_number} - {task.title} [{column_name}]"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_created_list.addItem(item)
            else:
                item = QtWidgets.QListWidgetItem("No tasks match filters")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                item.setForeground(QtGui.QColor(TEXT_MUTED))
                self.my_created_list.addItem(item)

            # Overdue tasks with severity grouping
            overdue_list = [t for t in all_tasks if t.assigned_to == user_id and t.is_overdue and not t.is_deleted]
            print(f"[MyTasks] Found {len(overdue_list)} overdue tasks")
            
            # Group by severity
            critical_overdue = []  # >7 days
            moderate_overdue = []  # 3-7 days
            recent_overdue = []    # 1-2 days
            
            for task in overdue_list:
                if task.deadline:
                    days_overdue = (today - task.deadline).days
                    if days_overdue > 7:
                        critical_overdue.append((task, days_overdue))
                    elif days_overdue >= 3:
                        moderate_overdue.append((task, days_overdue))
                    else:
                        recent_overdue.append((task, days_overdue))
            
            # Clear list completely (remove all items including placeholders)
            self.my_overdue_list.clear()
            while self.my_overdue_list.count() > 0:
                self.my_overdue_list.takeItem(0)
            
            print(f"[MyTasks] Adding {len(overdue_list)} tasks to Overdue list (Critical: {len(critical_overdue)}, Moderate: {len(moderate_overdue)}, Recent: {len(recent_overdue)})")
            
            # Critical overdue
            if critical_overdue:
                header = QtWidgets.QListWidgetItem(f"🔴 CRITICAL OVERDUE (>7 days) - {len(critical_overdue)} tasks")
                header.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                header.setForeground(QtGui.QColor("#EF4444"))
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                self.my_overdue_list.addItem(header)
                
                for task, days in sorted(critical_overdue, key=lambda x: x[1], reverse=True):
                    deadline_str = task.deadline.strftime('%Y-%m-%d')
                    item_text = f"  {task.task_number} - {task.title}\n  Due: {deadline_str} | {days} days overdue | Priority: {task.priority.upper()}"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_overdue_list.addItem(item)
            
            # Moderate overdue
            if moderate_overdue:
                if critical_overdue:  # Add spacing
                    spacer = QtWidgets.QListWidgetItem("")
                    spacer.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                    self.my_overdue_list.addItem(spacer)
                
                header = QtWidgets.QListWidgetItem(f"🟠 MODERATE OVERDUE (3-7 days) - {len(moderate_overdue)} tasks")
                header.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                header.setForeground(QtGui.QColor("#F59E0B"))
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                self.my_overdue_list.addItem(header)
                
                for task, days in sorted(moderate_overdue, key=lambda x: x[1], reverse=True):
                    deadline_str = task.deadline.strftime('%Y-%m-%d')
                    item_text = f"  {task.task_number} - {task.title}\n  Due: {deadline_str} | {days} days overdue | Priority: {task.priority.upper()}"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_overdue_list.addItem(item)
            
            # Recent overdue
            if recent_overdue:
                if critical_overdue or moderate_overdue:  # Add spacing
                    spacer = QtWidgets.QListWidgetItem("")
                    spacer.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                    self.my_overdue_list.addItem(spacer)
                
                header = QtWidgets.QListWidgetItem(f"🟡 RECENTLY OVERDUE (1-2 days) - {len(recent_overdue)} tasks")
                header.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                header.setForeground(QtGui.QColor("#FBBF24"))
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                self.my_overdue_list.addItem(header)
                
                for task, days in sorted(recent_overdue, key=lambda x: x[1], reverse=True):
                    deadline_str = task.deadline.strftime('%Y-%m-%d')
                    item_text = f"  {task.task_number} - {task.title}\n  Due: {deadline_str} | {days} days overdue | Priority: {task.priority.upper()}"
                    item = QtWidgets.QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, task.id)
                    self.my_overdue_list.addItem(item)

            if not critical_overdue and not moderate_overdue and not recent_overdue:
                item = QtWidgets.QListWidgetItem("✅ No overdue tasks")
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                item.setForeground(QtGui.QColor(SUCCESS))
                self.my_overdue_list.addItem(item)

        except Exception as e:
            print(f"Error refreshing my tasks: {e}")
            import traceback
            traceback.print_exc()

    def _on_my_task_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """Handle click on a task in My Tasks view."""
        if not self.manager or not self.auth_result:
            return  # Ignore clicks when not authenticated
        task_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if task_id:
            self._show_task_detail(task_id)

    def _on_my_tasks_filter_changed(self) -> None:
        """Handle filter changes in My Tasks view."""
        if self.manager and self.auth_result:
            self._refresh_my_tasks()

    def _clear_my_tasks_filters(self) -> None:
        """Clear all My Tasks filters."""
        self.my_tasks_search.clear()
        self.my_tasks_status_filter.setCurrentIndex(1)  # Reset to "Active Only"
        self.my_tasks_priority_filter.setCurrentIndex(0)  # Reset to "All Priorities"
        self.my_tasks_sort.setCurrentIndex(0)  # Reset to "Due Date"
        self._refresh_my_tasks()

    def _apply_my_tasks_filters(self, tasks: list) -> list:
        """Apply current filters to task list."""
        from datetime import date
        
        filtered = tasks
        
        # Search filter
        search_text = self.my_tasks_search.text().strip().lower()
        if search_text:
            filtered = [
                t for t in filtered
                if search_text in t.title.lower() 
                or (t.description and search_text in t.description.lower())
                or search_text in t.task_number.lower()
            ]
        
        # Status filter
        status_filter = self.my_tasks_status_filter.currentData()
        if status_filter == "active":
            # Active = not in Done column
            filtered = [t for t in filtered if t.column and t.column.name != "Done"]
        elif status_filter == "completed":
            # Completed = in Done column
            filtered = [t for t in filtered if t.column and t.column.name == "Done"]
        elif status_filter == "in_progress":
            filtered = [t for t in filtered if t.column and t.column.name == "In Progress"]
        elif status_filter == "review":
            filtered = [t for t in filtered if t.column and t.column.name == "Review"]
        elif status_filter == "blocked":
            filtered = [t for t in filtered if t.status == "blocked"]
        
        # Priority filter
        priority_filter = self.my_tasks_priority_filter.currentData()
        if priority_filter:
            filtered = [t for t in filtered if t.priority == priority_filter]
        
        # Sort
        sort_by = self.my_tasks_sort.currentData()
        if sort_by == "deadline":
            # Sort by deadline (earliest first), None deadlines at end
            filtered = sorted(filtered, key=lambda t: (t.deadline is None, t.deadline or date.max))
        elif sort_by == "priority":
            # Sort by priority (critical, high, medium, low)
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            filtered = sorted(filtered, key=lambda t: priority_order.get(t.priority, 4))
        elif sort_by == "updated":
            filtered = sorted(filtered, key=lambda t: t.updated_at or t.created_at, reverse=True)
        elif sort_by == "task_number":
            filtered = sorted(filtered, key=lambda t: t.task_number)
        
        return filtered

    def _refresh_reports(self) -> None:
        """Refresh the Reports view with current statistics and team performance."""
        if not self.manager:
            return

        try:
            from datetime import datetime, timedelta
            
            # Get statistics
            stats = self.manager.get_statistics()

            # Update stat cards
            total_card = self.total_tasks_card.findChild(QtWidgets.QLabel, "Total_value")
            if total_card:
                total_card.setText(str(stats.get("total_tasks", 0)))

            completed_card = self.completed_tasks_card.findChild(QtWidgets.QLabel, "Done_value")
            completed_subtitle = self.completed_tasks_card.findChild(QtWidgets.QLabel, "Done_subtitle")
            if completed_card:
                completed_count = stats.get("completed_tasks", 0)
                total_count = stats.get("total_tasks", 1)
                completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
                completed_card.setText(str(completed_count))
                if completed_subtitle:
                    completed_subtitle.setText(f"{completion_rate:.0f}%")

            in_progress_card = self.in_progress_card.findChild(QtWidgets.QLabel, "In Progress_value")
            if in_progress_card:
                in_progress = stats.get("in_progress_tasks", 0)
                in_progress_card.setText(str(in_progress))

            overdue_card = self.overdue_card.findChild(QtWidgets.QLabel, "Overdue_value")
            if overdue_card:
                overdue_card.setText(str(stats.get("overdue_tasks", 0)))

            # Team Performance Metrics
            self._refresh_team_performance()

        except Exception as e:
            print(f"Error refreshing reports: {e}")
            import traceback
            traceback.print_exc()

    def _on_reports_time_period_changed(self) -> None:
        """Handle time period selection change."""
        if self.manager:
            self._refresh_team_performance()

    def _refresh_team_performance(self) -> None:
        """Refresh team performance metrics table."""
        if not self.manager:
            return
        
        try:
            from datetime import datetime, timedelta, date
            
            # Get time period
            time_period = self.reports_time_period.currentData()
            
            # Calculate date range
            today = datetime.now().date()
            if time_period == "month":
                start_date = today.replace(day=1)
            elif time_period == "90days":
                start_date = today - timedelta(days=90)
            else:  # all time
                start_date = None
            
            # Get all users and tasks
            users = self.manager.get_all_users()
            all_tasks = self.manager.get_all_tasks()
            
            # Calculate performance for each user
            performance_data = []
            
            for user in users:
                if not user.is_active:
                    continue
                
                # Filter tasks for this user
                user_tasks = [t for t in all_tasks if t.assigned_to == user.id and not t.is_deleted]
                
                # Apply time period filter
                if start_date:
                    user_tasks = [t for t in user_tasks if t.created_at.date() >= start_date]
                
                # Calculate metrics
                total_assigned = len(user_tasks)
                if total_assigned == 0:
                    continue  # Skip users with no tasks
                
                # Active tasks (not in Done column)
                active = len([t for t in user_tasks if t.column and t.column.name != "Done"])
                
                # Done tasks (in Done column)
                done = len([t for t in user_tasks if t.column and t.column.name == "Done"])
                
                # Overdue tasks
                overdue = len([t for t in user_tasks if t.is_overdue])
                
                # On-time completion percentage
                done_with_deadline = [t for t in user_tasks 
                                     if t.column and t.column.name == "Done" 
                                     and t.deadline and t.completed_at]
                
                if done_with_deadline:
                    on_time_count = 0
                    for task in done_with_deadline:
                        completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
                        deadline_date = task.deadline if isinstance(task.deadline, date) else task.deadline
                        if completed_date <= deadline_date:
                            on_time_count += 1
                    on_time_pct = (on_time_count / len(done_with_deadline)) * 100
                else:
                    on_time_pct = None  # N/A
                
                # Average completion days
                if done > 0:
                    completion_times = []
                    for task in user_tasks:
                        if task.column and task.column.name == "Done" and task.completed_at:
                            completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
                            created_date = task.created_at.date() if isinstance(task.created_at, datetime) else task.created_at
                            days = (completed_date - created_date).days
                            completion_times.append(days)
                    avg_days = sum(completion_times) / len(completion_times) if completion_times else 0
                else:
                    avg_days = None  # N/A
                
                performance_data.append({
                    "name": user.display_name,
                    "active": active,
                    "done": done,
                    "on_time_pct": on_time_pct,
                    "overdue": overdue,
                    "avg_days": avg_days
                })
            
            # Add team/group performance
            groups = self.manager.get_all_groups()
            for group in groups:
                if not group.is_active:
                    continue
                
                # Get tasks for this group
                group_tasks = [t for t in all_tasks if t.assigned_group_id == group.id and not t.is_deleted]
                
                # Apply time period filter
                if start_date:
                    group_tasks = [t for t in group_tasks if t.created_at.date() >= start_date]
                
                if not group_tasks:
                    continue
                
                # Calculate metrics for group
                group_active = len([t for t in group_tasks if t.column and t.column.name != "Done"])
                group_done = len([t for t in group_tasks if t.column and t.column.name == "Done"])
                group_overdue = len([t for t in group_tasks if t.is_overdue])
                
                # On-time percentage for group
                done_with_deadline = [t for t in group_tasks 
                                     if t.column and t.column.name == "Done" 
                                     and t.deadline and t.completed_at]
                
                if done_with_deadline:
                    on_time_count = 0
                    for task in done_with_deadline:
                        completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
                        deadline_date = task.deadline if isinstance(task.deadline, date) else task.deadline
                        if completed_date <= deadline_date:
                            on_time_count += 1
                    group_on_time_pct = (on_time_count / len(done_with_deadline)) * 100
                else:
                    group_on_time_pct = None
                
                # Average days for group
                if group_done > 0:
                    completion_times = []
                    for task in group_tasks:
                        if task.column and task.column.name == "Done" and task.completed_at:
                            completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
                            created_date = task.created_at.date() if isinstance(task.created_at, datetime) else task.created_at
                            days = (completed_date - created_date).days
                            completion_times.append(days)
                    group_avg_days = sum(completion_times) / len(completion_times) if completion_times else 0
                else:
                    group_avg_days = None
                
                performance_data.append({
                    "name": f"👥 {group.name} (Team)",
                    "active": group_active,
                    "done": group_done,
                    "on_time_pct": group_on_time_pct,
                    "overdue": group_overdue,
                    "avg_days": group_avg_days
                })
            
            # Add unassigned tasks
            unassigned_tasks = [t for t in all_tasks if not t.assigned_to and not t.is_deleted]
            if start_date:
                unassigned_tasks = [t for t in unassigned_tasks if t.created_at.date() >= start_date]
            
            if unassigned_tasks:
                unassigned_active = len([t for t in unassigned_tasks if t.column and t.column.name != "Done"])
                unassigned_done = len([t for t in unassigned_tasks if t.column and t.column.name == "Done"])
                unassigned_overdue = len([t for t in unassigned_tasks if t.is_overdue])
                performance_data.append({
                    "name": UNASSIGNED_LABEL,
                    "active": unassigned_active,
                    "done": unassigned_done,
                    "on_time_pct": None,
                    "overdue": unassigned_overdue,
                    "avg_days": None
                })
            
            # Sort by overdue (desc), then active (desc)
            performance_data.sort(key=lambda x: (-x["overdue"], -x["active"]))
            
            # Update table
            self.performance_table.setRowCount(len(performance_data))
            
            for row, data in enumerate(performance_data):
                # Name
                name_item = QtWidgets.QTableWidgetItem(data["name"])
                self.performance_table.setItem(row, 0, name_item)
                
                # Active
                active_item = QtWidgets.QTableWidgetItem(str(data["active"]))
                active_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.performance_table.setItem(row, 1, active_item)
                
                # Done
                done_item = QtWidgets.QTableWidgetItem(str(data["done"]))
                done_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.performance_table.setItem(row, 2, done_item)
                
                # On-Time %
                if data["on_time_pct"] is not None:
                    on_time_pct = data["on_time_pct"]
                    on_time_text = f"{on_time_pct:.0f}%"
                    
                    # Add indicator
                    if on_time_pct >= 80:
                        on_time_text += " ✅"
                        color = SUCCESS
                    elif on_time_pct < 60:
                        on_time_text += " ⚠️"
                        color = WARNING
                    else:
                        color = TEXT_PRIMARY
                    
                    on_time_item = QtWidgets.QTableWidgetItem(on_time_text)
                    on_time_item.setForeground(QtGui.QColor(color))
                else:
                    on_time_item = QtWidgets.QTableWidgetItem("N/A")
                    on_time_item.setForeground(QtGui.QColor(TEXT_MUTED))
                
                on_time_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.performance_table.setItem(row, 3, on_time_item)
                
                # Overdue
                overdue_text = str(data["overdue"])
                if data["overdue"] > 5:
                    overdue_text += " 🔴"
                    color = WARNING
                else:
                    color = TEXT_PRIMARY
                
                overdue_item = QtWidgets.QTableWidgetItem(overdue_text)
                overdue_item.setForeground(QtGui.QColor(color))
                overdue_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.performance_table.setItem(row, 4, overdue_item)
                
                # Avg Days
                if data["avg_days"] is not None:
                    avg_days_item = QtWidgets.QTableWidgetItem(f"{data['avg_days']:.1f}")
                else:
                    avg_days_item = QtWidgets.QTableWidgetItem("N/A")
                    avg_days_item.setForeground(QtGui.QColor(TEXT_MUTED))
                
                avg_days_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.performance_table.setItem(row, 5, avg_days_item)
        
        except Exception as e:
            print(f"Error refreshing team performance: {e}")
            import traceback
            traceback.print_exc()

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
            
            # Populate group filter
            groups = self.manager.get_all_groups()
            self.group_filter.clear()
            self.group_filter.addItem("👥 All Groups", None)
            for group in groups:
                self.group_filter.addItem(f"👥 {group.name}", group.id)

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
        """Refresh tasks in all columns with pagination."""
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
            total_tasks = len(tasks)

            # Determine if pagination should be used
            use_pagination = self._should_use_pagination(tasks)
            
            # Get page size for this column (default to TASKS_PER_PAGE)
            page_size = self.column_page_sizes.get(column.id, self.TASKS_PER_PAGE)
            
            # Determine visible tasks
            if use_pagination and total_tasks > page_size:
                visible_tasks = tasks[:page_size]
            else:
                visible_tasks = tasks
                page_size = total_tasks  # Show all

            # Determine view mode based on task count
            view_mode = self._get_view_mode_for_column(column.id, total_tasks)

            # Add task cards
            if visible_tasks:
                for task in visible_tasks:
                    task_card = self._create_task_card(task, view_mode=view_mode, column_task_count=total_tasks)
                    layout.insertWidget(layout.count() - 1, task_card)
            elif total_tasks == 0:
                # Show empty state if no tasks
                empty_label = QtWidgets.QLabel("No tasks")
                empty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(f"color: {TEXT_MUTED}; padding: 20px; font-size: 11px;")
                layout.insertWidget(layout.count() - 1, empty_label)

            # Add pagination controls if needed
            if use_pagination and total_tasks > page_size:
                pagination_widget = self._create_pagination_controls(column.id, page_size, total_tasks)
                layout.insertWidget(layout.count() - 1, pagination_widget)

            # Update task count
            count_badge = column_widget.findChild(QtWidgets.QLabel, f"count_badge_{column.id}")
            if count_badge:
                if use_pagination and total_tasks > page_size:
                    count_badge.setText(f"{page_size}/{total_tasks}")
                else:
                    count_badge.setText(str(total_tasks))

            # WIP limit warning
            if column.wip_limit and total_tasks > column.wip_limit:
                wip_label = column_widget.findChild(QtWidgets.QLabel, f"wip_label_{column.id}")
                if wip_label:
                    wip_label.setStyleSheet(
                        f"font-size: 10px; color: {WARNING}; font-weight: 700; border: none; padding: 2px 0;"
                    )
                    wip_label.setText(f"⚠️ WIP Limit Exceeded: {total_tasks}/{column.wip_limit}")

    def _filter_tasks(self, tasks: list) -> list:
        """Apply current filters to task list."""
        filtered = tasks

        # Assignee filter
        assignee_id = self.assignee_filter.currentData()
        if assignee_id is not None:
            filtered = [t for t in filtered if t.assigned_to == assignee_id]

        # Group filter
        group_id = self.group_filter.currentData()
        if group_id is not None:
            filtered = [t for t in filtered if t.assigned_group_id == group_id]

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
                if search_text in t.title.lower() 
                or (t.description and search_text in t.description.lower())
                or search_text in t.task_number.lower()
            ]

        return filtered

    def _create_task_card(self, task, view_mode: str = 'detailed', column_task_count: int = 0) -> QtWidgets.QWidget:
        """Create a task card widget with specified view mode."""
        card = DraggableTaskCard(task)
        card.clicked.connect(self._show_task_detail)

        # Choose layout based on view mode
        if view_mode == 'mini':
            return self._create_mini_card_layout(card, task)
        elif view_mode == 'compact':
            return self._create_compact_card_layout(card, task)
        else:  # detailed
            return self._create_detailed_card_layout(card, task)

    def _create_detailed_card_layout(self, card: DraggableTaskCard, task) -> QtWidgets.QWidget:
        """Create detailed card layout (for <20 tasks)."""
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Task number and priority
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(6)

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

    def _create_compact_card_layout(self, card: DraggableTaskCard, task) -> QtWidgets.QWidget:
        """Create compact card layout (for 20-50 tasks) - fits in 240-320px column."""
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)

        # Row 1: Task number and priority
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(3)

        task_num = QtWidgets.QLabel(task.task_number)
        task_num.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px; font-weight: 600; border: none;")
        header.addWidget(task_num)

        # Priority badge (compact)
        priority_colors = {
            "critical": "#EF4444",
            "high": "#F59E0B",
            "medium": "#3B82F6",
            "low": "#10B981",
        }
        priority_badge = QtWidgets.QLabel(task.priority[0].upper())  # Just first letter
        priority_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {priority_colors.get(task.priority, '#3B82F6')};
                color: white;
                border-radius: 2px;
                padding: 1px 3px;
                font-size: 7px;
                font-weight: 700;
            }}
            """
        )
        header.addWidget(priority_badge)
        header.addStretch()

        layout.addLayout(header)

        # Row 2: Title (single line, same as mini view)
        title_text = task.title if len(task.title) <= 35 else task.title[:35] + "..."
        title = QtWidgets.QLabel(title_text)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10px; font-weight: 600; border: none;")
        title.setWordWrap(False)
        layout.addWidget(title)

        # Row 3: Metadata (stacked if needed)
        meta = QtWidgets.QHBoxLayout()
        meta.setSpacing(4)

        # Assignee/Group (compact)
        if task.assigned_group:
            group_label = QtWidgets.QLabel(f"👥 {task.assigned_group.name[:10]}")
            group_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; border: none;")
            meta.addWidget(group_label)
        elif task.assignee:
            assignee_name = task.assignee.display_name.split()[0]  # First name only
            assignee_label = QtWidgets.QLabel(f"👤 {assignee_name}")
            assignee_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; border: none;")
            meta.addWidget(assignee_label)

        if task.deadline:
            deadline_label = QtWidgets.QLabel(f"📅 {task.deadline.strftime('%m/%d')}")
            if task.is_overdue:
                deadline_label.setStyleSheet(f"color: #EF4444; font-size: 8px; font-weight: 700; border: none;")
            else:
                deadline_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; border: none;")
            meta.addWidget(deadline_label)

        if task.comment_count > 0:
            comment_label = QtWidgets.QLabel(f"💬{task.comment_count}")
            comment_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; border: none;")
            meta.addWidget(comment_label)

        meta.addStretch()
        layout.addLayout(meta)

        return card

    def _create_mini_card_layout(self, card: DraggableTaskCard, task) -> QtWidgets.QWidget:
        """Create mini card layout (for >50 tasks) - fits in 240-320px column."""
        # Use vertical layout for better fit in narrow columns
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)

        # Row 1: Task number and priority dot
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(3)
        
        task_num = QtWidgets.QLabel(task.task_number)
        task_num.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 8px; font-weight: 600; border: none;")
        header.addWidget(task_num)

        # Priority indicator (colored dot)
        priority_colors = {
            "critical": "#EF4444",
            "high": "#F59E0B",
            "medium": "#3B82F6",
            "low": "#10B981",
        }
        priority_dot = QtWidgets.QLabel("●")
        priority_dot.setStyleSheet(f"color: {priority_colors.get(task.priority, '#3B82F6')}; font-size: 10px; border: none;")
        header.addWidget(priority_dot)
        header.addStretch()
        
        layout.addLayout(header)

        # Row 2: Title (truncated but readable)
        title_text = task.title if len(task.title) <= 35 else task.title[:35] + "..."
        title = QtWidgets.QLabel(title_text)
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 9px; border: none;")
        title.setWordWrap(False)
        layout.addWidget(title)

        # Row 3: Quick info (if available)
        if task.deadline or task.assignee:
            meta = QtWidgets.QHBoxLayout()
            meta.setSpacing(3)
            
            if task.assignee:
                assignee_name = task.assignee.display_name.split()[0][:6]  # First name, max 6 chars
                assignee_label = QtWidgets.QLabel(f"👤{assignee_name}")
                assignee_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 7px; border: none;")
                meta.addWidget(assignee_label)
            
            if task.deadline:
                deadline_label = QtWidgets.QLabel(f"📅{task.deadline.strftime('%m/%d')}")
                if task.is_overdue:
                    deadline_label.setStyleSheet(f"color: #EF4444; font-size: 7px; font-weight: 700; border: none;")
                else:
                    deadline_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 7px; border: none;")
                meta.addWidget(deadline_label)
            
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

    def _refresh_filters(self) -> None:
        """Refresh filter dropdowns (users and groups)."""
        if not self.manager:
            return
        
        # Save current selections
        current_user = self.assignee_filter.currentData()
        current_group = self.group_filter.currentData()
        current_priority = self.priority_filter.currentData()
        
        # Refresh user filter
        users = self.manager.get_all_users()
        self.assignee_filter.clear()
        self.assignee_filter.addItem("👤 All Users", None)
        for user in users:
            self.assignee_filter.addItem(f"👤 {user.display_name}", user.id)
        
        # Restore user selection if still valid
        if current_user is not None:
            index = self.assignee_filter.findData(current_user)
            if index >= 0:
                self.assignee_filter.setCurrentIndex(index)
        
        # Refresh group filter
        groups = self.manager.get_all_groups()
        self.group_filter.clear()
        self.group_filter.addItem("👥 All Groups", None)
        for group in groups:
            self.group_filter.addItem(f"👥 {group.name}", group.id)
        
        # Restore group selection if still valid
        if current_group is not None:
            index = self.group_filter.findData(current_group)
            if index >= 0:
                self.group_filter.setCurrentIndex(index)

    def _refresh_board(self) -> None:
        """Refresh the entire board."""
        if not self._ensure_authenticated():
            return
        self._refresh_filters()
        self._refresh_tasks()
        if self.auth_result:
            update_last_activity(self.auth_result.session.session_token, db_manager=self.db)
        QtWidgets.QMessageBox.information(self, "Board Refreshed", "The Kanban board has been refreshed successfully.")

    def _on_search_changed(self) -> None:
        """Handle search text changes."""
        search_text = self.search_input.text().strip()
        self._refresh_tasks()
        
        # Update search results counter
        if search_text:
            # Count visible tasks across all columns
            total_visible = 0
            for column_id, column_widget in self.column_widgets.items():
                tasks_container = column_widget.findChild(QtWidgets.QWidget, f"tasks_container_{column_id}")
                if tasks_container:
                    # Count task card widgets (exclude headers, spacers)
                    layout = tasks_container.layout()
                    for i in range(layout.count() - 1):  # Exclude stretch
                        item = layout.itemAt(i)
                        if item and item.widget() and isinstance(item.widget(), DraggableTaskCard):
                            total_visible += 1
            
            self.search_results_label.setText(f"✓ {total_visible} found")
            self.search_results_label.setVisible(True)
        else:
            self.search_results_label.setVisible(False)

    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        # Reset pagination when filters change
        self.column_page_sizes = {}
        self._refresh_tasks()

    def _should_use_pagination(self, tasks: list) -> bool:
        """Determine if pagination should be used for this task list."""
        # If filters/search active, disable pagination (show all results)
        if self.search_input.text().strip():
            return False
        if self.assignee_filter.currentData() is not None:
            return False
        if self.priority_filter.currentData() is not None:
            return False
        if self.group_filter.currentData() is not None:
            return False
        
        # Only paginate if >30 tasks and no filters
        return len(tasks) > 30

    def _get_view_mode_for_column(self, column_id: int, task_count: int) -> str:
        """Determine view mode based on task count."""
        # Check if manually set
        if column_id in self.column_view_modes:
            mode = self.column_view_modes[column_id]
            if mode != 'auto':
                return mode
        
        # Auto-determine based on count
        if task_count < 20:
            return 'detailed'
        elif task_count <= 50:
            return 'compact'
        else:
            return 'mini'

    def _create_pagination_controls(self, column_id: int, shown: int, total: int) -> QtWidgets.QWidget:
        """Create pagination control widgets."""
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"background-color: {SURFACE_BG}; border-radius: 6px; padding: 8px;")
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Status label
        status_label = QtWidgets.QLabel(f"Showing {shown} of {total}")
        status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600;")
        layout.addWidget(status_label)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(4)
        
        # Load More button
        remaining = total - shown
        load_more_btn = QtWidgets.QPushButton(f"Load More ({remaining})")
        load_more_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_PRIMARY};
                font-size: 10px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {CARD_BG};
                border-color: {ACCENT};
            }}
            """
        )
        load_more_btn.clicked.connect(lambda: self._load_more_tasks(column_id))
        button_layout.addWidget(load_more_btn)
        
        # View All button
        view_all_btn = QtWidgets.QPushButton(f"View All ({total})")
        view_all_btn.setStyleSheet(load_more_btn.styleSheet())
        view_all_btn.clicked.connect(lambda: self._load_all_tasks(column_id))
        button_layout.addWidget(view_all_btn)
        
        layout.addLayout(button_layout)
        
        return container

    def _load_more_tasks(self, column_id: int) -> None:
        """Load 20 more tasks for a column."""
        current_size = self.column_page_sizes.get(column_id, self.TASKS_PER_PAGE)
        self.column_page_sizes[column_id] = current_size + self.TASKS_PER_PAGE
        self._refresh_tasks()

    def _load_all_tasks(self, column_id: int) -> None:
        """Load all tasks for a column."""
        self.column_page_sizes[column_id] = 999999  # Large number to show all
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
        self._refresh_filters()
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


