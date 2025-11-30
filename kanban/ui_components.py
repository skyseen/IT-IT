"""UI components for Kanban: dialogs, task cards, etc."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from kanban.auth import (
    AuthenticationError,
    AuthorizationError,
    admin_reset_password,
    authenticate,
    change_password,
)
from kanban.database import DatabaseManager
from kanban.manager import KanbanManager
from kanban.models import KanbanUser

# Import color constants
try:
    from ui import ACCENT, CARD_BG, ELEVATED_BG, TEXT_MUTED, TEXT_PRIMARY, WARNING
except ImportError:
    ACCENT = "#38BDF8"
    CARD_BG = "#1E293B"
    ELEVATED_BG = "#334155"
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_MUTED = "#94A3B8"
    WARNING = "#FBBF24"


class NewTaskDialog(QtWidgets.QDialog):
    """Dialog for creating a new task."""

    def __init__(self, manager: KanbanManager, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Create New Task")
        self.setMinimumWidth(600)
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: #0F172A;
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
                padding: 8px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {ACCENT};
            }}
            QPushButton {{
                background-color: {ELEVATED_BG};
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 10px 20px;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 189, 248, 0.2);
                border-color: {ACCENT};
            }}
            QPushButton#submitBtn {{
                background-color: {ACCENT};
                border: none;
                color: #051221;
            }}
            QPushButton#submitBtn:hover {{
                background-color: rgba(56, 189, 248, 0.9);
            }}
            """
        )

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title_label = QtWidgets.QLabel("Create New Task")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {ACCENT};")
        layout.addWidget(title_label)

        # Form
        form = QtWidgets.QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # Task title (required)
        self.title_input = QtWidgets.QLineEdit()
        self.title_input.setPlaceholderText("Enter task title...")
        form.addRow("Title *:", self.title_input)

        # Description
        self.description_input = QtWidgets.QTextEdit()
        self.description_input.setPlaceholderText("Enter task description...")
        self.description_input.setMinimumHeight(80)
        self.description_input.setMaximumHeight(200)
        form.addRow("Description:", self.description_input)

        # Column
        self.column_combo = QtWidgets.QComboBox()
        columns = self.manager.get_all_columns()
        for col in columns:
            self.column_combo.addItem(f"{col.name}", col.id)
        form.addRow("Column:", self.column_combo)

        # Assignment type selector
        assign_type_layout = QtWidgets.QHBoxLayout()
        
        self.assign_type_combo = QtWidgets.QComboBox()
        self.assign_type_combo.addItem("👤 Individual User", "user")
        self.assign_type_combo.addItem("👥 Group", "group")
        self.assign_type_combo.currentIndexChanged.connect(self._on_assign_type_changed)
        assign_type_layout.addWidget(self.assign_type_combo)
        
        form.addRow("Assign Type:", assign_type_layout)
        
        # Assignee (User)
        self.assignee_combo = QtWidgets.QComboBox()
        self.assignee_combo.addItem("Unassigned", None)
        users = self.manager.get_all_users()
        for user in users:
            self.assignee_combo.addItem(user.display_name, user.id)
        self.assignee_label = QtWidgets.QLabel("Assign To User:")
        form.addRow(self.assignee_label, self.assignee_combo)
        
        # Assignee (Group)
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItem("No Group", None)
        groups = self.manager.get_all_groups()
        for group in groups:
            self.group_combo.addItem(f"👥 {group.name} ({group.member_count} members)", group.id)
        self.group_label = QtWidgets.QLabel("Assign To Group:")
        form.addRow(self.group_label, self.group_combo)
        self.group_combo.hide()
        self.group_label.hide()

        # Priority
        self.priority_combo = QtWidgets.QComboBox()
        self.priority_combo.addItem("🟢 Low", "low")
        self.priority_combo.addItem("🟡 Medium", "medium")
        self.priority_combo.addItem("🟠 High", "high")
        self.priority_combo.addItem("🔴 Critical", "critical")
        self.priority_combo.setCurrentIndex(1)  # Default to Medium
        form.addRow("Priority:", self.priority_combo)

        # Category
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("General", "general")
        self.category_combo.addItem("SAP", "sap")
        self.category_combo.addItem("Agile", "agile")
        self.category_combo.addItem("Telco", "telco")
        self.category_combo.addItem("User Ops", "user_ops")
        form.addRow("Category:", self.category_combo)

        # Deadline
        self.deadline_input = QtWidgets.QDateEdit()
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setDate(QtCore.QDate.currentDate().addDays(7))
        self.deadline_input.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Deadline:", self.deadline_input)

        # Estimated hours
        self.hours_input = QtWidgets.QDoubleSpinBox()
        self.hours_input.setRange(0, 999)
        self.hours_input.setValue(0)
        self.hours_input.setSuffix(" hours")
        form.addRow("Est. Hours:", self.hours_input)

        # Tags
        self.tags_input = QtWidgets.QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags...")
        form.addRow("Tags:", self.tags_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QtWidgets.QPushButton("Create Task")
        create_btn.setObjectName("submitBtn")
        create_btn.clicked.connect(self._create_task)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)

    def _on_assign_type_changed(self) -> None:
        """Handle assignment type change."""
        assign_type = self.assign_type_combo.currentData()
        
        # Toggle visibility using the stored label references
        if assign_type == "user":
            self.assignee_combo.show()
            self.assignee_label.show()
            self.group_combo.hide()
            self.group_label.hide()
        else:  # group
            self.assignee_combo.hide()
            self.assignee_label.hide()
            self.group_combo.show()
            self.group_label.show()

    def _create_task(self) -> None:
        """Create the task and close dialog."""
        # Validate title
        title = self.title_input.text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Task title is required!")
            return

        try:
            # Parse tags
            tags_text = self.tags_input.text().strip()
            tags = [t.strip() for t in tags_text.split(",") if t.strip()] if tags_text else []

            # Get deadline
            deadline_qdate = self.deadline_input.date()
            deadline = date(deadline_qdate.year(), deadline_qdate.month(), deadline_qdate.day())

            # Determine assignment
            assign_type = self.assign_type_combo.currentData()
            assigned_to = self.assignee_combo.currentData() if assign_type == "user" else None
            assigned_group_id = self.group_combo.currentData() if assign_type == "group" else None

            # Create task
            task = self.manager.create_task(
                title=title,
                description=self.description_input.toPlainText().strip() or None,
                column_id=self.column_combo.currentData(),
                assigned_to=assigned_to,
                assigned_group_id=assigned_group_id,
                priority=self.priority_combo.currentData(),
                category=self.category_combo.currentData(),
                deadline=deadline,
                estimated_hours=self.hours_input.value() if self.hours_input.value() > 0 else None,
                tags=tags,
            )

            QtWidgets.QMessageBox.information(
                self, "Success", f"Task {task.task_number} created successfully!"
            )
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create task:\n{str(e)}")


class TaskDetailDialog(QtWidgets.QDialog):
    """Dialog for viewing and editing task details."""

    def __init__(
        self, task_id: int, manager: KanbanManager, parent: Optional[QtWidgets.QWidget] = None
    ):
        super().__init__(parent)
        self.task_id = task_id
        self.manager = manager
        self.task = None

        self.setWindowTitle("Task Details")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setStyleSheet(NewTaskDialog(manager).styleSheet())  # Reuse style

        self._load_task()
        self._init_ui()

    def _load_task(self) -> None:
        """Load task from database."""
        self.task = self.manager.get_task(self.task_id)
        if not self.task:
            QtWidgets.QMessageBox.critical(self, "Error", f"Task {self.task_id} not found!")
            self.reject()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with task number
        header = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel(f"{self.task.task_number}: {self.task.title}")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {ACCENT};")
        title_label.setWordWrap(True)
        header.addWidget(title_label, 1)

        # Delete button
        delete_btn = QtWidgets.QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #EF4444;
                border: none;
                color: white;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            """
        )
        delete_btn.clicked.connect(self._delete_task)
        header.addWidget(delete_btn)

        layout.addLayout(header)

        # Tabs for different sections
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._create_details_tab(), "📝 Details")
        tabs.addTab(self._create_comments_tab(), "💬 Comments")
        tabs.addTab(self._create_activity_tab(), "📊 Activity")

        layout.addWidget(tabs, 1)

        # Bottom buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        save_btn = QtWidgets.QPushButton("Save Changes")
        save_btn.setObjectName("submitBtn")
        save_btn.clicked.connect(self._save_changes)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_details_tab(self) -> QtWidgets.QWidget:
        """Create the details tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setSpacing(12)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # Title
        self.edit_title = QtWidgets.QLineEdit(self.task.title)
        form.addRow("Title:", self.edit_title)

        # Description
        self.edit_description = QtWidgets.QTextEdit(self.task.description or "")
        self.edit_description.setMinimumHeight(100)
        self.edit_description.setMaximumHeight(250)
        self.edit_description.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        form.addRow("Description:", self.edit_description)

        # Column
        self.edit_column = QtWidgets.QComboBox()
        columns = self.manager.get_all_columns()
        for col in columns:
            self.edit_column.addItem(col.name, col.id)
            if col.id == self.task.column_id:
                self.edit_column.setCurrentIndex(self.edit_column.count() - 1)
        form.addRow("Column:", self.edit_column)

        # Assignment type selector
        self.edit_assign_type = QtWidgets.QComboBox()
        self.edit_assign_type.addItem("👤 Individual User", "user")
        self.edit_assign_type.addItem("👥 Group", "group")
        
        # Set initial type based on current assignment
        if self.task.assigned_group_id:
            self.edit_assign_type.setCurrentIndex(1)  # Group
        else:
            self.edit_assign_type.setCurrentIndex(0)  # User
        
        self.edit_assign_type.currentIndexChanged.connect(self._on_edit_assign_type_changed)
        form.addRow("Assign Type:", self.edit_assign_type)
        
        # Assignee (User)
        self.edit_assignee = QtWidgets.QComboBox()
        self.edit_assignee.addItem("Unassigned", None)
        users = self.manager.get_all_users()
        for user in users:
            self.edit_assignee.addItem(user.display_name, user.id)
            if user.id == self.task.assigned_to:
                self.edit_assignee.setCurrentIndex(self.edit_assignee.count() - 1)
        self.edit_assignee_label = QtWidgets.QLabel("Assigned To User:")
        form.addRow(self.edit_assignee_label, self.edit_assignee)
        
        # Assignee (Group)
        self.edit_group = QtWidgets.QComboBox()
        self.edit_group.addItem("No Group", None)
        groups = self.manager.get_all_groups()
        for group in groups:
            self.edit_group.addItem(f"👥 {group.name} ({group.member_count} members)", group.id)
            if group.id == self.task.assigned_group_id:
                self.edit_group.setCurrentIndex(self.edit_group.count() - 1)
        self.edit_group_label = QtWidgets.QLabel("Assigned To Group:")
        form.addRow(self.edit_group_label, self.edit_group)
        
        # Toggle visibility based on current assignment
        if self.task.assigned_group_id:
            self.edit_assignee.hide()
            self.edit_assignee_label.hide()
        else:
            self.edit_group.hide()
            self.edit_group_label.hide()

        # Priority
        self.edit_priority = QtWidgets.QComboBox()
        priorities = [("🟢 Low", "low"), ("🟡 Medium", "medium"), ("🟠 High", "high"), ("🔴 Critical", "critical")]
        for label, value in priorities:
            self.edit_priority.addItem(label, value)
            if value == self.task.priority:
                self.edit_priority.setCurrentIndex(self.edit_priority.count() - 1)
        form.addRow("Priority:", self.edit_priority)

        # Status
        self.edit_status = QtWidgets.QComboBox()
        statuses = ["active", "blocked", "completed", "archived"]
        for status in statuses:
            self.edit_status.addItem(status.capitalize(), status)
            if status == self.task.status:
                self.edit_status.setCurrentIndex(self.edit_status.count() - 1)
        form.addRow("Status:", self.edit_status)

        # Category
        self.edit_category = QtWidgets.QComboBox()
        categories = ["general", "sap", "agile", "telco", "user_ops"]
        for cat in categories:
            self.edit_category.addItem(cat.capitalize(), cat)
            if cat == self.task.category:
                self.edit_category.setCurrentIndex(self.edit_category.count() - 1)
        form.addRow("Category:", self.edit_category)

        # Deadline
        self.edit_deadline = QtWidgets.QDateEdit()
        self.edit_deadline.setCalendarPopup(True)
        self.edit_deadline.setDisplayFormat("yyyy-MM-dd")
        if self.task.deadline:
            self.edit_deadline.setDate(
                QtCore.QDate(self.task.deadline.year, self.task.deadline.month, self.task.deadline.day)
            )
        form.addRow("Deadline:", self.edit_deadline)
        
        # Overdue/Late completion status indicator
        if self.task.is_overdue:
            overdue_label = QtWidgets.QLabel("⚠️ Task is OVERDUE")
            overdue_label.setStyleSheet("""
                color: #EF4444;
                font-weight: 700;
                background: rgba(239, 68, 68, 0.1);
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid #EF4444;
            """)
            form.addRow("", overdue_label)
        elif self.task.was_completed_late:
            late_label = QtWidgets.QLabel("⏰ Completed Late")
            late_label.setStyleSheet("""
                color: #F59E0B;
                font-weight: 600;
                background: rgba(245, 158, 11, 0.1);
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid #F59E0B;
            """)
            form.addRow("", late_label)

        # Estimated hours
        self.edit_estimated = QtWidgets.QDoubleSpinBox()
        self.edit_estimated.setRange(0, 999)
        self.edit_estimated.setValue(float(self.task.estimated_hours or 0))
        self.edit_estimated.setSuffix(" hours")
        form.addRow("Est. Hours:", self.edit_estimated)

        # Actual hours
        self.edit_actual = QtWidgets.QDoubleSpinBox()
        self.edit_actual.setRange(0, 999)
        self.edit_actual.setValue(float(self.task.actual_hours or 0))
        self.edit_actual.setSuffix(" hours")
        form.addRow("Actual Hours:", self.edit_actual)

        # Tags
        self.edit_tags = QtWidgets.QLineEdit(",".join(self.task.tags or []))
        form.addRow("Tags:", self.edit_tags)

        # Metadata (read-only)
        meta_group = QtWidgets.QGroupBox("Metadata")
        meta_layout = QtWidgets.QFormLayout(meta_group)

        creator_label = QtWidgets.QLabel(self.task.creator.display_name if self.task.creator else "Unknown")
        creator_label.setStyleSheet(f"color: {TEXT_MUTED};")
        meta_layout.addRow("Created By:", creator_label)

        created_label = QtWidgets.QLabel(self.task.created_at.strftime("%Y-%m-%d %H:%M") if self.task.created_at else "N/A")
        created_label.setStyleSheet(f"color: {TEXT_MUTED};")
        meta_layout.addRow("Created At:", created_label)

        updated_label = QtWidgets.QLabel(self.task.updated_at.strftime("%Y-%m-%d %H:%M") if self.task.updated_at else "N/A")
        updated_label.setStyleSheet(f"color: {TEXT_MUTED};")
        meta_layout.addRow("Updated At:", updated_label)

        form.addRow(meta_group)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return tab

    def _create_comments_tab(self) -> QtWidgets.QWidget:
        """Create the comments tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Comments list
        comments_scroll = QtWidgets.QScrollArea()
        comments_scroll.setWidgetResizable(True)
        comments_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.comments_container = QtWidgets.QWidget()
        self.comments_layout = QtWidgets.QVBoxLayout(self.comments_container)
        self.comments_layout.setSpacing(8)
        self.comments_layout.addStretch()

        comments_scroll.setWidget(self.comments_container)
        layout.addWidget(comments_scroll, 1)

        # Add comment input
        input_layout = QtWidgets.QHBoxLayout()

        self.comment_input = QtWidgets.QLineEdit()
        self.comment_input.setPlaceholderText("Add a comment...")
        input_layout.addWidget(self.comment_input, 1)

        add_btn = QtWidgets.QPushButton("💬 Add Comment")
        add_btn.setObjectName("submitBtn")
        add_btn.clicked.connect(self._add_comment)
        input_layout.addWidget(add_btn)

        layout.addLayout(input_layout)

        # Load comments
        self._load_comments()

        return tab

    def _create_activity_tab(self) -> QtWidgets.QWidget:
        """Create the activity/history tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        # Activity list
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        activity_container = QtWidgets.QWidget()
        self.activity_layout = QtWidgets.QVBoxLayout(activity_container)
        self.activity_layout.setSpacing(8)
        self.activity_layout.addStretch()

        scroll.setWidget(activity_container)
        layout.addWidget(scroll)

        # Load activity log
        self._load_activity_log()

        return tab

    def _load_activity_log(self) -> None:
        """Load and display activity log from database."""
        try:
            # Get activity log for this task
            session = self.manager.db.get_session()
            from kanban.models import KanbanActivityLog, KanbanUser
            from datetime import datetime

            activities = (
                session.query(KanbanActivityLog, KanbanUser)
                .outerjoin(KanbanUser, KanbanActivityLog.user_id == KanbanUser.id)
                .filter(KanbanActivityLog.task_id == self.task_id)
                .order_by(KanbanActivityLog.id.desc())
                .all()
            )
            
            print(f"[ActivityLog] Loaded {len(activities)} activities for task {self.task_id}")
            for activity_log, user in activities:
                print(f"[ActivityLog]   - ID:{activity_log.id} Type:{activity_log.activity_type} Field:{activity_log.field_name} Old:{activity_log.old_value} New:{activity_log.new_value}")

            # Clear existing
            while self.activity_layout.count() > 1:
                item = self.activity_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not activities:
                no_activity = QtWidgets.QLabel("No activity recorded yet.")
                no_activity.setStyleSheet("color: #94A3B8; font-style: italic; padding: 20px;")
                no_activity.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.activity_layout.insertWidget(0, no_activity)
                return

            # Add activity items
            for activity_log, user in activities:
                activity_widget = self._create_activity_item(activity_log, user)
                self.activity_layout.insertWidget(self.activity_layout.count() - 1, activity_widget)

            session.close()

        except Exception as e:
            print(f"Error loading activity log: {e}")
            import traceback
            traceback.print_exc()

    def _create_activity_item(self, activity: "KanbanActivityLog", user: Optional["KanbanUser"]) -> QtWidgets.QWidget:
        """Create a single activity item widget."""
        from datetime import datetime

        item = QtWidgets.QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border-left: 3px solid #38BDF8;
                border-radius: 6px;
                padding: 12px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(item)
        layout.setSpacing(4)

        # Header: user + timestamp
        header = QtWidgets.QHBoxLayout()
        user_name = user.display_name if user else "System"
        user_label = QtWidgets.QLabel(f"👤 {user_name}")
        user_label.setStyleSheet("font-weight: 600; color: #F1F5F9;")
        header.addWidget(user_label)

        header.addStretch()

        # Format timestamp
        time_ago = self._format_time_ago(activity.created_at)
        time_label = QtWidgets.QLabel(time_ago)
        time_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        header.addWidget(time_label)

        layout.addLayout(header)

        # Action description
        action_text = self._format_activity_action(activity)
        action_label = QtWidgets.QLabel(action_text)
        action_label.setWordWrap(True)
        action_label.setStyleSheet("color: #CBD5E1; font-size: 13px;")
        layout.addWidget(action_label)

        # Show changes if available
        if activity.old_value or activity.new_value:
            changes_text = ""
            if activity.old_value:
                changes_text += f"FROM: {activity.old_value}\n"
            if activity.new_value:
                changes_text += f"TO: {activity.new_value}"
            
            if changes_text:
                changes_label = QtWidgets.QLabel(changes_text)
                changes_label.setStyleSheet("""
                    color: #94A3B8;
                    font-size: 12px;
                    font-weight: 600;
                    background: rgba(15, 23, 42, 0.8);
                    padding: 8px 10px;
                    border-radius: 4px;
                    margin-top: 4px;
                    border-left: 3px solid #38BDF8;
                """)
                changes_label.setWordWrap(True)
                layout.addWidget(changes_label)

        return item

    def _format_activity_action(self, activity: "KanbanActivityLog") -> str:
        """Format activity action into human-readable text."""
        action = activity.activity_type
        field = activity.field_name or ""

        action_map = {
            "created": "✨ Created this task",
            "task_created": "✨ Created this task",
            "updated": f"✏️ Updated {field}" if field else "✏️ Updated task",
            "task_updated": f"✏️ Updated {field}" if field else "✏️ Updated task",
            "moved": "➡️ Moved task",
            "task_moved": "➡️ Moved task",
            "assigned": f"👤 Assigned task to {activity.new_value}" if activity.new_value else "👤 Updated assignment",
            "unassigned": "👤 Unassigned task",
            "commented": "💬 Added a comment",
            "comment_added": "💬 Added a comment",
            "deleted": "🗑️ Deleted this task",
            "task_deleted": "🗑️ Deleted this task",
            "status_changed": f"🔄 Changed status to {activity.new_value}" if activity.new_value else "🔄 Changed status",
        }

        return action_map.get(action, f"⚡ {action.replace('_', ' ').title()}")

    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as 'time ago' string."""
        from datetime import datetime, timedelta

        if not timestamp:
            return "Unknown time"

        now = datetime.now()
        if timestamp.tzinfo:
            # If timestamp has timezone, make now aware too
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        
        diff = now - timestamp

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff < timedelta(days=30):
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return timestamp.strftime("%Y-%m-%d %H:%M")

    def _load_comments(self) -> None:
        """Load and display comments."""
        comments = self.manager.get_comments(self.task_id)

        # Clear existing
        while self.comments_layout.count() > 1:
            item = self.comments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add comment widgets
        for comment in comments:
            comment_widget = self._create_comment_widget(comment)
            self.comments_layout.insertWidget(self.comments_layout.count() - 1, comment_widget)

    def _create_comment_widget(self, comment) -> QtWidgets.QWidget:
        """Create a comment widget."""
        widget = QtWidgets.QFrame()
        widget.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 6px;
                padding: 10px;
            }}
            """
        )

        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(6)

        # Header
        header = QtWidgets.QHBoxLayout()

        user_label = QtWidgets.QLabel(f"👤 {comment.user.display_name}")
        user_label.setStyleSheet(f"color: {ACCENT}; font-weight: 600; font-size: 12px;")
        header.addWidget(user_label)

        time_label = QtWidgets.QLabel(comment.created_at.strftime("%Y-%m-%d %H:%M") if comment.created_at else "")
        time_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        header.addWidget(time_label)

        header.addStretch()
        layout.addLayout(header)

        # Comment text
        text_label = QtWidgets.QLabel(comment.comment)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
        layout.addWidget(text_label)

        return widget

    def _add_comment(self) -> None:
        """Add a new comment."""
        text = self.comment_input.text().strip()
        if not text:
            return

        try:
            self.manager.add_comment(self.task_id, text)
            self.comment_input.clear()
            self._load_comments()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add comment:\n{str(e)}")

    def _on_edit_assign_type_changed(self) -> None:
        """Handle assignment type change in edit mode."""
        assign_type = self.edit_assign_type.currentData()
        
        # Toggle visibility using the stored label references
        if assign_type == "user":
            self.edit_assignee.show()
            self.edit_assignee_label.show()
            self.edit_group.hide()
            self.edit_group_label.hide()
        else:  # group
            self.edit_assignee.hide()
            self.edit_assignee_label.hide()
            self.edit_group.show()
            self.edit_group_label.show()

    def _save_changes(self) -> None:
        """Save task changes."""
        try:
            # Parse tags
            tags_text = self.edit_tags.text().strip()
            tags = [t.strip() for t in tags_text.split(",") if t.strip()] if tags_text else []

            # Get deadline
            deadline_qdate = self.edit_deadline.date()
            deadline_date = date(deadline_qdate.year(), deadline_qdate.month(), deadline_qdate.day())

            # Check if column changed (move task)
            new_column_id = self.edit_column.currentData()
            if new_column_id != self.task.column_id:
                self.manager.move_task(self.task_id, new_column_id)

            # Determine assignment based on type
            assign_type = self.edit_assign_type.currentData()
            assigned_to = self.edit_assignee.currentData() if assign_type == "user" else None
            assigned_group_id = self.edit_group.currentData() if assign_type == "group" else None

            # Update other fields
            updates = {
                "title": self.edit_title.text().strip(),
                "description": self.edit_description.toPlainText().strip() or None,
                "assigned_to": assigned_to,
                "assigned_group_id": assigned_group_id,
                "priority": self.edit_priority.currentData(),
                "status": self.edit_status.currentData(),
                "category": self.edit_category.currentData(),
                "deadline": deadline_date,
                "estimated_hours": self.edit_estimated.value() if self.edit_estimated.value() > 0 else None,
                "actual_hours": self.edit_actual.value() if self.edit_actual.value() > 0 else None,
                "tags": tags,
            }

            self.manager.update_task(self.task_id, **updates)

            QtWidgets.QMessageBox.information(self, "Success", "Task updated successfully!")
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update task:\n{str(e)}")

    def _delete_task(self) -> None:
        """Delete the task."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete task {self.task.task_number}?\n\nThis action can be undone (soft delete).",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                self.manager.delete_task(self.task_id, hard_delete=False)
                QtWidgets.QMessageBox.information(self, "Success", "Task deleted successfully!")
                self.accept()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete task:\n{str(e)}")


class LoginDialog(QtWidgets.QDialog):
    """Dialog for authenticating a Kanban user."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        remembered_username: str | None = None,
        allow_cancel: bool = False,
    ) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.auth_result = None
        self.allow_cancel = allow_cancel

        self.setWindowTitle("Kanban Login")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Sign in to Kanban")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        if remembered_username:
            self.username_input.setText(remembered_username)
        form.addRow("Username:", self.username_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        remember_layout = QtWidgets.QHBoxLayout()
        self.remember_checkbox = QtWidgets.QCheckBox("Remember me on this device")
        self.remember_checkbox.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #38BDF8;
                border-radius: 4px;
                background-color: #1E293B;
            }
            QCheckBox::indicator:checked {
                background-color: #38BDF8;
                border-color: #38BDF8;
                image: url(none);
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
            }
            QCheckBox::indicator:hover {
                border-color: #60A5FA;
                background-color: #334155;
            }
        """)
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        form.addRow("", remember_layout)

        layout.addLayout(form)

        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: #EF4444;")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        if allow_cancel:
            cancel_btn = QtWidgets.QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            buttons.addWidget(cancel_btn)
        login_btn = QtWidgets.QPushButton("Sign In")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self._attempt_login)
        buttons.addWidget(login_btn)

        layout.addLayout(buttons)

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._attempt_login)

    def _attempt_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember = self.remember_checkbox.isChecked()

        if not username or not password:
            self._show_error("Username and password are required.")
            return

        try:
            self.auth_result = authenticate(
                username,
                password,
                remember_me=remember,
                db_manager=self.db_manager,
            )
        except AuthenticationError as exc:
            self._show_error(str(exc))
            return

        self.accept()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()


class ChangePasswordDialog(QtWidgets.QDialog):
    """Dialog for self-service password change."""

    def __init__(
        self,
        user: KanbanUser,
        db_manager: DatabaseManager,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.user = user
        self.db_manager = db_manager

        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Change your password")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)

        self.current_input = QtWidgets.QLineEdit()
        self.current_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("Current password:", self.current_input)

        self.new_input = QtWidgets.QLineEdit()
        self.new_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("New password:", self.new_input)

        self.confirm_input = QtWidgets.QLineEdit()
        self.confirm_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        form.addRow("Confirm password:", self.confirm_input)

        layout.addLayout(form)

        hint = QtWidgets.QLabel(
            "Password must be at least 8 characters and include upper/lowercase, a digit, and a symbol."
        )
        hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(hint)

        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: #EF4444;")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        save_btn = QtWidgets.QPushButton("Update Password")
        save_btn.clicked.connect(self._change_password)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def _change_password(self) -> None:
        current = self.current_input.text()
        new = self.new_input.text()
        confirm = self.confirm_input.text()

        if not current or not new:
            self._show_error("All fields are required.")
            return

        if new != confirm:
            self._show_error("New passwords do not match.")
            return

        try:
            change_password(self.user.id, current, new, db_manager=self.db_manager)
        except AuthenticationError as exc:
            self._show_error(str(exc))
            return

        QtWidgets.QMessageBox.information(self, "Password Updated", "Password updated successfully.")
        self.accept()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()


class AdminPasswordResetDialog(QtWidgets.QDialog):
    """Dialog for admins to reset another user's password."""

    def __init__(
        self,
        admin_user: KanbanUser,
        db_manager: DatabaseManager,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.admin_user = admin_user
        self.db_manager = db_manager
        self.generated_password = None

        self.setWindowTitle("Reset User Password")
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Reset a user's password")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)

        self.user_combo = QtWidgets.QComboBox()
        self._populate_users()
        form.addRow("User:", self.user_combo)

        self.temp_password_input = QtWidgets.QLineEdit()
        self.temp_password_input.setPlaceholderText("Leave blank to auto-generate")
        form.addRow("Temporary password:", self.temp_password_input)

        self.force_reset_checkbox = QtWidgets.QCheckBox("Require password change on next login")
        self.force_reset_checkbox.setChecked(True)
        form.addRow("", self.force_reset_checkbox)

        layout.addLayout(form)

        self.result_box = QtWidgets.QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setFixedHeight(120)
        self.result_box.hide()
        layout.addWidget(self.result_box)

        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: #EF4444;")
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)
        reset_btn = QtWidgets.QPushButton("Reset Password")
        reset_btn.clicked.connect(self._reset_password)
        buttons.addWidget(reset_btn)
        layout.addLayout(buttons)

    def _populate_users(self) -> None:
        session = self.db_manager.get_session()
        try:
            users = (
                session.query(KanbanUser)
                .filter(KanbanUser.is_active == True)  # noqa: E712
                .order_by(KanbanUser.display_name)
                .all()
            )
            for user in users:
                if user.id == self.admin_user.id:
                    continue
                display = f"{user.display_name} ({user.username})"
                self.user_combo.addItem(display, user.id)
        finally:
            session.close()

    def _reset_password(self) -> None:
        target_id = self.user_combo.currentData()
        if target_id is None:
            self._show_error("No user selected.")
            return

        temp_password = self.temp_password_input.text().strip() or None
        force_reset = self.force_reset_checkbox.isChecked()

        try:
            new_password = admin_reset_password(
                self.admin_user,
                target_user_id=target_id,
                new_password=temp_password,
                force_reset=force_reset,
                db_manager=self.db_manager,
            )
        except AuthorizationError as exc:
            self._show_error(str(exc))
            return
        except AuthenticationError as exc:
            self._show_error(str(exc))
            return

        self.result_box.setPlainText(
            "Password reset successful.\n"
            f"Temporary password: {new_password}\n"
            "Share this password securely with the user."
        )
        self.result_box.show()
        self.error_label.hide()

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()
        self.result_box.hide()


class GroupManagementDialog(QtWidgets.QDialog):
    """Dialog for managing groups."""

    def __init__(self, manager: KanbanManager, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.manager = manager

        self.setWindowTitle("Manage Groups")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0F172A;
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 8px;
                color: {TEXT_PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {ACCENT};
            }}
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: #051221;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 189, 248, 0.9);
            }}
            QPushButton:disabled {{
                background-color: {ELEVATED_BG};
                color: {TEXT_MUTED};
            }}
        """)

        self._init_ui()
        self._refresh_groups()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QtWidgets.QLabel("👥 Group Management")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {ACCENT};")
        layout.addWidget(title)

        # Split view: Groups list on left, details on right
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Left panel: Groups list
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Create new group button
        new_group_btn = QtWidgets.QPushButton("➕ New Group")
        new_group_btn.clicked.connect(self._create_group)
        left_layout.addWidget(new_group_btn)

        # Groups list
        self.groups_list = QtWidgets.QListWidget()
        self.groups_list.setStyleSheet(f"""
            QListWidget {{
                background: {CARD_BG};
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid rgba(56, 189, 248, 0.1);
            }}
            QListWidget::item:selected {{
                background: {ACCENT};
                color: #051221;
            }}
            QListWidget::item:hover {{
                background: {ELEVATED_BG};
            }}
        """)
        self.groups_list.itemSelectionChanged.connect(self._on_group_selected)
        left_layout.addWidget(self.groups_list)

        splitter.addWidget(left_panel)

        # Right panel: Group details
        self.details_panel = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(12, 0, 0, 0)

        # Group details form
        form = QtWidgets.QFormLayout()
        form.setSpacing(12)

        self.group_name_edit = QtWidgets.QLineEdit()
        form.addRow("Group Name:", self.group_name_edit)

        self.group_desc_edit = QtWidgets.QTextEdit()
        self.group_desc_edit.setMaximumHeight(80)
        form.addRow("Description:", self.group_desc_edit)

        self.group_color_btn = QtWidgets.QPushButton("Choose Color")
        self.group_color_btn.clicked.connect(self._choose_color)
        self.selected_color = "#60A5FA"
        self.group_color_btn.setStyleSheet(f"background-color: {self.selected_color};")
        form.addRow("Color:", self.group_color_btn)

        details_layout.addLayout(form)

        # Action buttons
        action_btns = QtWidgets.QHBoxLayout()
        
        self.save_group_btn = QtWidgets.QPushButton("💾 Save")
        self.save_group_btn.clicked.connect(self._save_group)
        action_btns.addWidget(self.save_group_btn)

        self.delete_group_btn = QtWidgets.QPushButton("🗑️ Delete")
        self.delete_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.delete_group_btn.clicked.connect(self._delete_group)
        action_btns.addWidget(self.delete_group_btn)

        details_layout.addLayout(action_btns)

        # Members section
        members_label = QtWidgets.QLabel("Group Members")
        members_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 20px;")
        details_layout.addWidget(members_label)

        # Add member controls
        add_member_layout = QtWidgets.QHBoxLayout()
        
        self.user_combo = QtWidgets.QComboBox()
        add_member_layout.addWidget(self.user_combo, 1)

        add_member_btn = QtWidgets.QPushButton("➕ Add")
        add_member_btn.clicked.connect(self._add_member)
        add_member_layout.addWidget(add_member_btn)

        details_layout.addLayout(add_member_layout)

        # Members list
        self.members_list = QtWidgets.QListWidget()
        self.members_list.setStyleSheet(self.groups_list.styleSheet())
        details_layout.addWidget(self.members_list)

        # Remove member button
        remove_member_btn = QtWidgets.QPushButton("➖ Remove Selected")
        remove_member_btn.clicked.connect(self._remove_member)
        details_layout.addWidget(remove_member_btn)

        # Hide details panel initially
        self.details_panel.setEnabled(False)

        splitter.addWidget(self.details_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.current_group_id = None

    def _refresh_groups(self) -> None:
        """Refresh the groups list."""
        self.groups_list.clear()
        groups = self.manager.get_all_groups()
        
        for group in groups:
            item = QtWidgets.QListWidgetItem(f"👥 {group.name}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, group.id)
            self.groups_list.addItem(item)

        # Refresh user combo
        self.user_combo.clear()
        users = self.manager.get_all_users()
        for user in users:
            self.user_combo.addItem(user.display_name, user.id)

    def _on_group_selected(self) -> None:
        """Handle group selection."""
        selected_items = self.groups_list.selectedItems()
        if not selected_items:
            self.details_panel.setEnabled(False)
            return

        group_id = selected_items[0].data(QtCore.Qt.ItemDataRole.UserRole)
        self.current_group_id = group_id

        # Load group details
        group = self.manager.get_group(group_id)
        if group:
            self.group_name_edit.setText(group.name)
            self.group_desc_edit.setText(group.description or "")
            self.selected_color = group.color
            self.group_color_btn.setStyleSheet(f"background-color: {self.selected_color};")
            
            # Load members
            self._refresh_members()
            
            self.details_panel.setEnabled(True)

    def _refresh_members(self) -> None:
        """Refresh the members list for current group."""
        if not self.current_group_id:
            return

        self.members_list.clear()
        members = self.manager.get_group_members(self.current_group_id)
        
        for member in members:
            item = QtWidgets.QListWidgetItem(f"👤 {member.display_name}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, member.id)
            self.members_list.addItem(item)

    def _create_group(self) -> None:
        """Create a new group."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Group", "Enter group name:"
        )
        
        if ok and name.strip():
            try:
                self.manager.create_group(name.strip())
                self._refresh_groups()
                QtWidgets.QMessageBox.information(self, "Success", f"Group '{name}' created!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create group:\n{str(e)}")

    def _save_group(self) -> None:
        """Save group changes."""
        if not self.current_group_id:
            return

        name = self.group_name_edit.text().strip()
        description = self.group_desc_edit.toPlainText().strip()

        if not name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Group name cannot be empty!")
            return

        try:
            self.manager.update_group(
                self.current_group_id,
                name=name,
                description=description or None,
                color=self.selected_color
            )
            self._refresh_groups()
            QtWidgets.QMessageBox.information(self, "Success", "Group updated!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update group:\n{str(e)}")

    def _delete_group(self) -> None:
        """Delete the current group."""
        if not self.current_group_id:
            return

        group = self.manager.get_group(self.current_group_id)
        if not group:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete group '{group.name}'?\n\n"
            "Tasks assigned to this group will become unassigned.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                self.manager.delete_group(self.current_group_id)
                self.current_group_id = None
                self.details_panel.setEnabled(False)
                self._refresh_groups()
                QtWidgets.QMessageBox.information(self, "Success", "Group deleted!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete group:\n{str(e)}")

    def _choose_color(self) -> None:
        """Choose a color for the group."""
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.selected_color), self, "Choose Group Color")
        
        if color.isValid():
            self.selected_color = color.name()
            self.group_color_btn.setStyleSheet(f"background-color: {self.selected_color};")

    def _add_member(self) -> None:
        """Add a member to the current group."""
        if not self.current_group_id:
            return

        user_id = self.user_combo.currentData()
        if not user_id:
            return

        try:
            self.manager.add_group_member(self.current_group_id, user_id)
            self._refresh_members()
            QtWidgets.QMessageBox.information(self, "Success", "Member added!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Warning", str(e))

    def _remove_member(self) -> None:
        """Remove selected member from the group."""
        if not self.current_group_id:
            return

        selected_items = self.members_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Warning", "No member selected!")
            return

        user_id = selected_items[0].data(QtCore.Qt.ItemDataRole.UserRole)
        
        try:
            self.manager.remove_group_member(self.current_group_id, user_id)
            self._refresh_members()
            QtWidgets.QMessageBox.information(self, "Success", "Member removed!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to remove member:\n{str(e)}")


