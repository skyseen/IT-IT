"""Main Kanban board UI component."""

from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from config_manager import get_active_profile_name
from kanban.database import get_db_manager
from kanban.manager import KanbanManager

# Import color constants from ui.py
try:
    from ui import ACCENT, CARD_BG, ELEVATED_BG, INFO, SUCCESS, TEXT_MUTED, TEXT_PRIMARY, WARNING
except ImportError:
    # Fallback if ui.py is not available
    ACCENT = "#38BDF8"
    CARD_BG = "#1E293B"
    ELEVATED_BG = "#334155"
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    SUCCESS = "#34D399"
    WARNING = "#FBBF24"
    INFO = "#60A5FA"


class KanbanBoardWidget(QtWidgets.QWidget):
    """Main Kanban board widget displaying columns and task cards."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.db = None
        self.manager = None
        self.current_user = None
        self.columns = []
        self.column_widgets = {}

        self._init_database()
        self._init_ui()
        self._load_board()

    def _init_database(self) -> None:
        """Initialize database connection and manager."""
        try:
            self.db = get_db_manager()
            if not self.db.test_connection():
                self._show_error("Database connection failed!")
                return

            # Get current user (for now, use first active user)
            # TODO: Implement proper user login/session management
            session = self.db.get_session()
            from kanban.models import KanbanUser

            self.current_user = session.query(KanbanUser).filter_by(is_active=True).first()
            session.close()

            if not self.current_user:
                self._show_error("No active users found! Please run seed_kanban_data.py first.")
                return

            self.manager = KanbanManager(self.db, current_user_id=self.current_user.id)

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

        # Board scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Board container
        self.board_container = QtWidgets.QWidget()
        self.board_layout = QtWidgets.QHBoxLayout(self.board_container)
        self.board_layout.setContentsMargins(20, 20, 20, 20)
        self.board_layout.setSpacing(16)
        self.board_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.board_container)
        main_layout.addWidget(scroll, 1)

    def _create_toolbar(self) -> QtWidgets.QWidget:
        """Create the toolbar with filters and actions."""
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
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        # Title
        title = QtWidgets.QLabel("📋 Kanban Board")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY}; border: none;")
        layout.addWidget(title)

        # Search box
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search tasks...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
            """
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Filter by assignee
        self.assignee_filter = QtWidgets.QComboBox()
        self.assignee_filter.setFixedWidth(180)
        self.assignee_filter.addItem("👤 All Users", None)
        self.assignee_filter.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
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
        layout.addWidget(self.assignee_filter)

        # Filter by priority
        self.priority_filter = QtWidgets.QComboBox()
        self.priority_filter.setFixedWidth(150)
        self.priority_filter.addItem("🎯 All Priorities", None)
        self.priority_filter.addItem("🔴 Critical", "critical")
        self.priority_filter.addItem("🟠 High", "high")
        self.priority_filter.addItem("🟡 Medium", "medium")
        self.priority_filter.addItem("🟢 Low", "low")
        self.priority_filter.setStyleSheet(self.assignee_filter.styleSheet())
        self.priority_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.priority_filter)

        layout.addStretch()

        # Refresh button
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(
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
        refresh_btn.clicked.connect(self._refresh_board)
        layout.addWidget(refresh_btn)

        # New Task button
        new_task_btn = QtWidgets.QPushButton("➕ New Task")
        new_task_btn.setFixedHeight(36)
        new_task_btn.setStyleSheet(
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
        new_task_btn.clicked.connect(self._create_new_task)
        layout.addWidget(new_task_btn)

        return toolbar

    def _load_board(self) -> None:
        """Load columns and tasks from database."""
        if not self.manager:
            return

        try:
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
        column_container = QtWidgets.QFrame()
        column_container.setFixedWidth(320)
        column_container.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 12px;
            }}
            """
        )

        layout = QtWidgets.QVBoxLayout(column_container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Column header
        header = QtWidgets.QHBoxLayout()

        color_dot = QtWidgets.QLabel("●")
        color_dot.setStyleSheet(f"color: {column.color}; font-size: 16px; border: none;")
        header.addWidget(color_dot)

        name_label = QtWidgets.QLabel(column.name)
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {TEXT_PRIMARY}; border: none;")
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
        card = QtWidgets.QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 12px;
            }}
            QFrame:hover {{
                border-color: {ACCENT};
                background-color: {ELEVATED_BG};
            }}
            """
        )
        card.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

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

        # Task metadata
        meta = QtWidgets.QHBoxLayout()

        if task.assignee:
            assignee_label = QtWidgets.QLabel(f"👤 {task.assignee.display_name}")
            assignee_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; border: none;")
            meta.addWidget(assignee_label)

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

        # Click to open detail dialog
        card.mousePressEvent = lambda event: self._open_task_detail(task.id)

        return card

    def _refresh_board(self) -> None:
        """Refresh the entire board."""
        self._refresh_tasks()
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

    def _open_task_detail(self, task_id: int) -> None:
        """Open task detail dialog."""
        from kanban.ui_components import TaskDetailDialog

        dialog = TaskDetailDialog(task_id, self.manager, parent=self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._refresh_tasks()

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


