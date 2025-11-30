"""SQLAlchemy ORM models for Kanban database."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_session, relationship

Base = declarative_base()


class KanbanUser(Base):
    """User model for Kanban system."""

    __tablename__ = "kanban_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    email = Column(String(200))
    role = Column(String(50), default="member")  # admin, member, viewer
    avatar_color = Column(String(7), default="#60A5FA")
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    password_hash = Column(String(255))
    password_last_changed = Column(DateTime)
    password_reset_required = Column(Boolean, default=False)

    # Audit fields
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("kanban_users.id"))
    last_login = Column(DateTime)

    # Metadata
    preferences = Column(JSON, default=dict)

    # Relationships
    created_tasks = relationship("KanbanTask", foreign_keys="KanbanTask.created_by", back_populates="creator")
    assigned_tasks = relationship("KanbanTask", foreign_keys="KanbanTask.assigned_to", back_populates="assignee")
    activity_logs = relationship("KanbanActivityLog", back_populates="user")
    comments = relationship("KanbanComment", back_populates="user")
    sessions = relationship("KanbanSession", back_populates="user")

    def __repr__(self) -> str:
        return f"<KanbanUser(id={self.id}, username='{self.username}', display_name='{self.display_name}')>"


class KanbanGroup(Base):
    """Group model for assigning multiple users to tasks."""

    __tablename__ = "kanban_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7), default="#60A5FA")  # Display color for UI
    is_active = Column(Boolean, default=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("kanban_users.id"))
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    modified_by = Column(Integer, ForeignKey("kanban_users.id"))

    # Relationships
    members = relationship("KanbanGroupMember", back_populates="group", cascade="all, delete-orphan")
    assigned_tasks = relationship("KanbanTask", back_populates="assigned_group")

    def __repr__(self) -> str:
        return f"<KanbanGroup(id={self.id}, name='{self.name}')>"
    
    @property
    def member_count(self) -> int:
        """Get count of active members in group."""
        if hasattr(self, '_member_count'):
            return self._member_count
        
        session = object_session(self)
        if not session or not self.id:
            return 0
        
        from sqlalchemy import func
        count = (
            session.query(func.count(KanbanGroupMember.id))
            .filter(KanbanGroupMember.group_id == self.id)
            .scalar()
        )
        return count or 0


class KanbanGroupMember(Base):
    """Junction table for group membership."""

    __tablename__ = "kanban_group_members"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("kanban_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("kanban_users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Member role within group (optional future feature)
    role = Column(String(50), default="member")  # lead, member
    
    # Audit
    added_at = Column(DateTime, default=datetime.now)
    added_by = Column(Integer, ForeignKey("kanban_users.id"))

    # Relationships
    group = relationship("KanbanGroup", back_populates="members")
    user = relationship("KanbanUser", foreign_keys=[user_id])

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    def __repr__(self) -> str:
        return f"<KanbanGroupMember(group_id={self.group_id}, user_id={self.user_id})>"


class KanbanColumn(Base):
    """Column model for Kanban board."""

    __tablename__ = "kanban_columns"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False)
    color = Column(String(7), default="#94A3B8")
    wip_limit = Column(Integer)  # Work-in-progress limit
    is_active = Column(Boolean, default=True)
    description = Column(Text)

    # Audit fields
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey("kanban_users.id"))
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    modified_by = Column(Integer, ForeignKey("kanban_users.id"))

    # Relationships
    tasks = relationship("KanbanTask", back_populates="column", order_by="KanbanTask.position")

    __table_args__ = (UniqueConstraint("name", "is_active", name="uq_column_name_active"),)

    def __repr__(self) -> str:
        return f"<KanbanColumn(id={self.id}, name='{self.name}', position={self.position})>"


class KanbanTask(Base):
    """Task/Card model for Kanban board."""

    __tablename__ = "kanban_tasks"

    id = Column(Integer, primary_key=True)

    # Basic Info
    title = Column(String(500), nullable=False)
    description = Column(Text)
    task_number = Column(String(50), unique=True)  # TASK-0001

    # Organization
    column_id = Column(Integer, ForeignKey("kanban_columns.id"), nullable=False, index=True)
    position = Column(Numeric(10, 2), nullable=False)  # REAL for flexible reordering

    # Assignment & Ownership
    assigned_to = Column(Integer, ForeignKey("kanban_users.id"), index=True)
    assigned_group_id = Column(Integer, ForeignKey("kanban_groups.id"), index=True)  # Group assignment
    created_by = Column(Integer, ForeignKey("kanban_users.id"), nullable=False)

    # Priority & Status
    priority = Column(String(20), default="medium", index=True)  # low, medium, high, critical
    status = Column(String(50), default="active", index=True)  # active, blocked, completed, archived

    # Categorization
    category = Column(String(50), index=True)  # sap, agile, telco, user_ops, general, etc.
    tags = Column(ARRAY(Text))  # Array of tags
    color = Column(String(7))  # Optional custom card color

    # Time Tracking
    deadline = Column(Date, index=True)
    estimated_hours = Column(Numeric(6, 2))
    actual_hours = Column(Numeric(6, 2), default=0)

    # Optional Workflow Integration
    is_workflow_task = Column(Boolean, default=False)
    workflow_type = Column(String(50))  # sap_creation, agile_reset, etc.
    workflow_reference = Column(String(200))  # Ticket #, Employee ID, etc.
    workflow_metadata = Column(JSON)  # Flexible storage

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    started_at = Column(DateTime)  # When moved to "In Progress"
    completed_at = Column(DateTime)  # When moved to "Done"

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer, ForeignKey("kanban_users.id"))

    # Relationships
    column = relationship("KanbanColumn", back_populates="tasks")
    assignee = relationship("KanbanUser", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    assigned_group = relationship("KanbanGroup", foreign_keys=[assigned_group_id], back_populates="assigned_tasks")
    creator = relationship("KanbanUser", foreign_keys=[created_by], back_populates="created_tasks")
    activity_logs = relationship("KanbanActivityLog", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("KanbanComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("KanbanAttachment", back_populates="task", cascade="all, delete-orphan")
    dependencies_from = relationship(
        "KanbanDependency",
        foreign_keys="KanbanDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependencies_to = relationship(
        "KanbanDependency",
        foreign_keys="KanbanDependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<KanbanTask(id={self.id}, task_number='{self.task_number}', title='{self.title}')>"

    @property
    def is_overdue(self) -> bool:
        """
        Check if task is currently overdue.
        
        A task is NOT overdue if:
        - No deadline is set
        - Status is "archived" (hidden from workflow)
        - In "Done" column (workflow complete)
        - Already completed
        
        A task IS overdue if:
        - Has a deadline
        - Deadline has passed
        - Not in Done column and not archived
        """
        if not self.deadline:
            return False
        
        # If archived, never show as overdue
        if self.status == "archived":
            return False
        
        # If in Done column, workflow is complete (not overdue)
        if self.column and self.column.name == "Done":
            return False
        
        # Check if deadline has passed
        today = datetime.now().date()
        return today > self.deadline
    
    @property
    def was_completed_late(self) -> bool:
        """
        Check if task was completed after its deadline.
        Useful for performance metrics and reporting.
        
        Returns True only if:
        - Task has a deadline
        - Task has a completed_at timestamp
        - Task was completed after the deadline
        """
        if not self.deadline or not self.completed_at:
            return False
        
        completed_date = self.completed_at.date() if isinstance(self.completed_at, datetime) else self.completed_at
        return completed_date > self.deadline

    @property
    def comment_count(self) -> int:
        """Get count of non-deleted comments."""
        comments = self.__dict__.get("comments")
        if comments is not None:
            return len([c for c in comments if not c.is_deleted])

        session = object_session(self)
        if not session or not self.id:
            return 0

        return (
            session.query(KanbanComment)
            .filter(KanbanComment.task_id == self.id, KanbanComment.is_deleted == False)  # noqa: E712
            .count()
        )

    @property
    def attachment_count(self) -> int:
        """Get count of non-deleted attachments."""
        attachments = self.__dict__.get("attachments")
        if attachments is not None:
            return len([a for a in attachments if not a.is_deleted])

        session = object_session(self)
        if not session or not self.id:
            return 0

        return (
            session.query(KanbanAttachment)
            .filter(KanbanAttachment.task_id == self.id, KanbanAttachment.is_deleted == False)  # noqa: E712
            .count()
        )


class KanbanActivityLog(Base):
    """Activity log model for comprehensive audit trail."""

    __tablename__ = "kanban_activity_log"

    id = Column(Integer, primary_key=True)

    # What happened
    task_id = Column(Integer, ForeignKey("kanban_tasks.id", ondelete="SET NULL"), index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    # Types: created, updated, deleted, moved, assigned, unassigned, commented, etc.

    # Who did it
    user_id = Column(Integer, ForeignKey("kanban_users.id"), nullable=False, index=True)

    # Details
    field_name = Column(String(100))  # Which field changed
    old_value = Column(Text)
    new_value = Column(Text)
    comment = Column(Text)  # For comment activities

    # Context
    ip_address = Column(String(45))  # User's IP
    user_agent = Column(Text)  # Application version

    # When
    created_at = Column(DateTime, default=datetime.now, index=True)

    # Full snapshot (for critical changes)
    task_snapshot = Column(JSON)  # Complete task state after change

    # Relationships
    task = relationship("KanbanTask", back_populates="activity_logs")
    user = relationship("KanbanUser", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<KanbanActivityLog(id={self.id}, type='{self.activity_type}', task_id={self.task_id})>"


class KanbanComment(Base):
    """Comment model for task discussions."""

    __tablename__ = "kanban_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("kanban_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("kanban_users.id"), nullable=False, index=True)
    comment = Column(Text, nullable=False)

    # Threading (optional - for replies)
    parent_comment_id = Column(Integer, ForeignKey("kanban_comments.id"))

    # Metadata
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    task = relationship("KanbanTask", back_populates="comments")
    user = relationship("KanbanUser", back_populates="comments")
    replies = relationship("KanbanComment", backref="parent", remote_side=[id])

    def __repr__(self) -> str:
        return f"<KanbanComment(id={self.id}, task_id={self.task_id}, user_id={self.user_id})>"


class KanbanAttachment(Base):
    """Attachment model for task files."""

    __tablename__ = "kanban_attachments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("kanban_tasks.id", ondelete="CASCADE"), nullable=False, index=True)

    # File info
    file_name = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))

    # Workflow attachment
    from_workflow = Column(Boolean, default=False)

    # Audit
    uploaded_by = Column(Integer, ForeignKey("kanban_users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer, ForeignKey("kanban_users.id"))

    # Relationships
    task = relationship("KanbanTask", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<KanbanAttachment(id={self.id}, file_name='{self.file_name}', task_id={self.task_id})>"


class KanbanDependency(Base):
    """Dependency model for task relationships."""

    __tablename__ = "kanban_dependencies"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("kanban_tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("kanban_tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type = Column(String(20), default="blocks")  # blocks, relates_to, duplicate_of

    # Audit
    created_by = Column(Integer, ForeignKey("kanban_users.id"))
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    task = relationship("KanbanTask", foreign_keys=[task_id], back_populates="dependencies_from")
    depends_on_task = relationship("KanbanTask", foreign_keys=[depends_on_task_id], back_populates="dependencies_to")

    __table_args__ = (UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency"),)

    def __repr__(self) -> str:
        return f"<KanbanDependency(task_id={self.task_id} depends_on {self.depends_on_task_id})>"


class KanbanSession(Base):
    """Session model for tracking active users."""

    __tablename__ = "kanban_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("kanban_users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False)
    remember_me = Column(Boolean, default=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)

    login_at = Column(DateTime, default=datetime.now)
    last_activity = Column(DateTime, default=datetime.now)
    logout_at = Column(DateTime)

    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    user = relationship("KanbanUser", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<KanbanSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class KanbanSettings(Base):
    """Settings model for system configuration."""

    __tablename__ = "kanban_settings"

    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text)

    # Audit
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    modified_by = Column(Integer, ForeignKey("kanban_users.id"))

    def __repr__(self) -> str:
        return f"<KanbanSettings(key='{self.setting_key}')>"


