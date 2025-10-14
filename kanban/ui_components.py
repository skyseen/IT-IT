"""UI components for Kanban: dialogs, task cards, etc."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from kanban.manager import KanbanManager

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
        self.description_input.setMaximumHeight(100)
        form.addRow("Description:", self.description_input)

        # Column
        self.column_combo = QtWidgets.QComboBox()
        columns = self.manager.get_all_columns()
        for col in columns:
            self.column_combo.addItem(f"{col.name}", col.id)
        form.addRow("Column:", self.column_combo)

        # Assignee
        self.assignee_combo = QtWidgets.QComboBox()
        self.assignee_combo.addItem("Unassigned", None)
        users = self.manager.get_all_users()
        for user in users:
            self.assignee_combo.addItem(user.display_name, user.id)
        form.addRow("Assign To:", self.assignee_combo)

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

            # Create task
            task = self.manager.create_task(
                title=title,
                description=self.description_input.toPlainText().strip() or None,
                column_id=self.column_combo.currentData(),
                assigned_to=self.assignee_combo.currentData(),
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
        self.edit_description.setMaximumHeight(150)
        form.addRow("Description:", self.edit_description)

        # Column
        self.edit_column = QtWidgets.QComboBox()
        columns = self.manager.get_all_columns()
        for col in columns:
            self.edit_column.addItem(col.name, col.id)
            if col.id == self.task.column_id:
                self.edit_column.setCurrentIndex(self.edit_column.count() - 1)
        form.addRow("Column:", self.edit_column)

        # Assignee
        self.edit_assignee = QtWidgets.QComboBox()
        self.edit_assignee.addItem("Unassigned", None)
        users = self.manager.get_all_users()
        for user in users:
            self.edit_assignee.addItem(user.display_name, user.id)
            if user.id == self.task.assigned_to:
                self.edit_assignee.setCurrentIndex(self.edit_assignee.count() - 1)
        form.addRow("Assigned To:", self.edit_assignee)

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

        activity_text = QtWidgets.QTextEdit()
        activity_text.setReadOnly(True)
        activity_text.setPlaceholderText("Activity history will be shown here...")

        # TODO: Load actual activity log from database
        activity_text.setText("Activity log not yet implemented.\n\nThis will show:\n- Task creation\n- All updates\n- Movements between columns\n- Assignments\n- Comments\n- Attachments")

        layout.addWidget(activity_text)

        return tab

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

            # Update other fields
            updates = {
                "title": self.edit_title.text().strip(),
                "description": self.edit_description.toPlainText().strip() or None,
                "assigned_to": self.edit_assignee.currentData(),
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


