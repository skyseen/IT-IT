"""Business logic and CRUD operations for Kanban system."""

from __future__ import annotations

import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from kanban.audit_logger import AuditLogger
from kanban.database import DatabaseManager
from kanban.models import (
    KanbanAttachment,
    KanbanColumn,
    KanbanComment,
    KanbanTask,
    KanbanUser,
)


class KanbanManager:
    """
    Core business logic for Kanban operations.
    All CRUD operations go through this class.
    """

    def __init__(self, db_manager: DatabaseManager, current_user_id: int, ip_address: Optional[str] = None):
        """
        Initialize Kanban manager.

        Args:
            db_manager: Database manager instance
            current_user_id: ID of the current user
            ip_address: Optional IP address of the user
        """
        self.db = db_manager
        self.current_user_id = current_user_id
        self.ip_address = ip_address
        self.logger = AuditLogger(db_manager)

    # -----------------------------------------------------------------------
    # Task CRUD Operations
    # -----------------------------------------------------------------------

    def create_task(
        self,
        title: str,
        column_id: int,
        description: Optional[str] = None,
        assigned_to: Optional[int] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        deadline: Optional[date] = None,
        estimated_hours: Optional[float] = None,
        tags: Optional[List[str]] = None,
        is_workflow_task: bool = False,
        workflow_type: Optional[str] = None,
        workflow_reference: Optional[str] = None,
        workflow_metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> KanbanTask:
        """
        Create a new task with full audit trail.

        Args:
            title: Task title (required)
            column_id: ID of the column to create task in
            description: Optional task description
            assigned_to: Optional user ID to assign task to
            priority: Task priority (low, medium, high, critical)
            category: Task category (sap, agile, telco, user_ops, general, etc.)
            deadline: Optional deadline date
            estimated_hours: Optional estimated hours
            tags: Optional list of tags
            is_workflow_task: Whether task is created from workflow
            workflow_type: Type of workflow (if is_workflow_task=True)
            workflow_reference: Workflow reference (ticket #, employee ID, etc.)
            workflow_metadata: Optional workflow metadata
            **kwargs: Additional task fields

        Returns:
            KanbanTask: Created task object

        Raises:
            ValueError: If validation fails
        """
        session = self.db.get_session()
        try:
            # Generate task number
            task_number = self._generate_task_number(session)

            # Get max position in column
            max_position = (
                session.query(func.max(KanbanTask.position))
                .filter_by(column_id=column_id, is_deleted=False)
                .scalar()
                or 0
            )

            # Create task
            task = KanbanTask(
                title=title,
                task_number=task_number,
                description=description,
                column_id=column_id,
                position=float(max_position) + 1.0,
                assigned_to=assigned_to,
                created_by=self.current_user_id,
                priority=priority,
                category=category,
                deadline=deadline,
                estimated_hours=estimated_hours,
                tags=tags or [],
                is_workflow_task=is_workflow_task,
                workflow_type=workflow_type,
                workflow_reference=workflow_reference,
                workflow_metadata=workflow_metadata,
            )

            session.add(task)
            session.flush()  # Get task ID before logging

            # Log creation
            self.logger.log_task_created(task, self.current_user_id)

            session.commit()
            return task

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_task(self, task_id: int) -> Optional[KanbanTask]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            KanbanTask or None if not found
        """
        session = self.db.get_session()
        try:
            task = (
                session.query(KanbanTask)
                .options(
                    joinedload(KanbanTask.assignee),
                    joinedload(KanbanTask.creator),
                    joinedload(KanbanTask.column),
                )
                .filter_by(id=task_id, is_deleted=False)
                .first()
            )
            return task
        finally:
            session.close()

    def update_task(self, task_id: int, **updates) -> KanbanTask:
        """
        Update task fields with change tracking.

        Args:
            task_id: Task ID
            **updates: Fields to update

        Returns:
            Updated task object

        Raises:
            ValueError: If task not found
        """
        session = self.db.get_session()
        try:
            task = (
                session.query(KanbanTask)
                .options(
                    joinedload(KanbanTask.assignee),
                    joinedload(KanbanTask.creator),
                    joinedload(KanbanTask.column),
                )
                .filter_by(id=task_id, is_deleted=False)
                .first()
            )
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # Track changes
            changes = {}
            for field, new_value in updates.items():
                if hasattr(task, field):
                    old_value = getattr(task, field)
                    if old_value != new_value:
                        changes[field] = {"old": old_value, "new": new_value}
                        setattr(task, field, new_value)

            # Log changes
            if changes:
                self.logger.log_task_updated(task, self.current_user_id, changes)

            session.commit()
            session.refresh(task)
            return task

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_task(self, task_id: int, hard_delete: bool = False) -> None:
        """
        Delete task (soft delete by default).

        Args:
            task_id: Task ID
            hard_delete: If True, permanently delete from database

        Raises:
            ValueError: If task not found
        """
        session = self.db.get_session()
        try:
            task = session.query(KanbanTask).filter_by(id=task_id).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            if hard_delete:
                # Permanent deletion
                self.logger.log_task_deleted(task, self.current_user_id)
                session.delete(task)
            else:
                # Soft delete
                task.is_deleted = True
                task.deleted_at = datetime.now()
                task.deleted_by = self.current_user_id
                self.logger.log_task_deleted(task, self.current_user_id)

            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def move_task(self, task_id: int, new_column_id: int, new_position: Optional[float] = None) -> KanbanTask:
        """
        Move task to different column with audit trail.

        Args:
            task_id: Task ID
            new_column_id: Target column ID
            new_position: Optional position in new column

        Returns:
            Updated task object

        Raises:
            ValueError: If task or column not found
        """
        session = self.db.get_session()
        try:
            task = session.query(KanbanTask).filter_by(id=task_id, is_deleted=False).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            column = session.query(KanbanColumn).filter_by(id=new_column_id, is_active=True).first()
            if not column:
                raise ValueError(f"Column {new_column_id} not found")

            old_column_id = task.column_id

            # Update position
            if new_position is None:
                max_pos = (
                    session.query(func.max(KanbanTask.position))
                    .filter_by(column_id=new_column_id, is_deleted=False)
                    .scalar()
                    or 0
                )
                new_position = float(max_pos) + 1.0

            task.column_id = new_column_id
            task.position = new_position

            # Track time (if moving to "In Progress" or "Done")
            if column.name == "In Progress" and not task.started_at:
                task.started_at = datetime.now()
            elif column.name == "Done" and not task.completed_at:
                task.completed_at = datetime.now()
                task.status = "completed"

            # Log move
            self.logger.log_task_moved(task, self.current_user_id, old_column_id, new_column_id)

            session.commit()
            return task

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_tasks_by_column(self, column_id: int) -> List[KanbanTask]:
        """
        Get all tasks in a column, ordered by position.

        Args:
            column_id: Column ID

        Returns:
            List of tasks
        """
        session = self.db.get_session()
        try:
            tasks = (
                session.query(KanbanTask)
                .options(
                    joinedload(KanbanTask.assignee),
                    joinedload(KanbanTask.creator),
                    joinedload(KanbanTask.column),
                )
                .filter_by(column_id=column_id, is_deleted=False)
                .order_by(KanbanTask.position)
                .all()
            )
            return tasks
        finally:
            session.close()

    def get_tasks_by_user(self, user_id: int) -> List[KanbanTask]:
        """
        Get all tasks assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of tasks
        """
        session = self.db.get_session()
        try:
            tasks = (
                session.query(KanbanTask)
                .options(
                    joinedload(KanbanTask.assignee),
                    joinedload(KanbanTask.creator),
                    joinedload(KanbanTask.column),
                )
                .filter_by(assigned_to=user_id, is_deleted=False)
                .order_by(KanbanTask.created_at.desc())
                .all()
            )
            return tasks
        finally:
            session.close()

    def search_tasks(self, query: str) -> List[KanbanTask]:
        """
        Search tasks by title and description.

        Args:
            query: Search query

        Returns:
            List of matching tasks
        """
        session = self.db.get_session()
        try:
            search_pattern = f"%{query}%"
            tasks = (
                session.query(KanbanTask)
                .options(
                    joinedload(KanbanTask.assignee),
                    joinedload(KanbanTask.creator),
                    joinedload(KanbanTask.column),
                )
                .filter(
                    (KanbanTask.title.ilike(search_pattern) | KanbanTask.description.ilike(search_pattern)),
                    KanbanTask.is_deleted == False,  # noqa: E712
                )
                .all()
            )
            return tasks
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Column Operations
    # -----------------------------------------------------------------------

    def get_all_columns(self) -> List[KanbanColumn]:
        """Get all active columns ordered by position."""
        session = self.db.get_session()
        try:
            columns = session.query(KanbanColumn).filter_by(is_active=True).order_by(KanbanColumn.position).all()
            return columns
        finally:
            session.close()

    def get_column_by_name(self, name: str) -> Optional[KanbanColumn]:
        """Get column by name."""
        session = self.db.get_session()
        try:
            column = session.query(KanbanColumn).filter_by(name=name, is_active=True).first()
            return column
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Comment Operations
    # -----------------------------------------------------------------------

    def add_comment(self, task_id: int, comment_text: str) -> KanbanComment:
        """
        Add a comment to a task.

        Args:
            task_id: Task ID
            comment_text: Comment text

        Returns:
            Created comment object

        Raises:
            ValueError: If task not found
        """
        session = self.db.get_session()
        try:
            task = session.query(KanbanTask).filter_by(id=task_id, is_deleted=False).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            comment = KanbanComment(
                task_id=task_id,
                user_id=self.current_user_id,
                comment=comment_text,
            )
            session.add(comment)
            session.flush()

            # Log comment addition
            self.logger.log_comment_added(comment, self.current_user_id)

            session.commit()
            return comment

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_comments(self, task_id: int) -> List[KanbanComment]:
        """Get all non-deleted comments for a task."""
        session = self.db.get_session()
        try:
            comments = (
                session.query(KanbanComment)
                .options(joinedload(KanbanComment.user))
                .filter_by(task_id=task_id, is_deleted=False)
                .order_by(KanbanComment.created_at)
                .all()
            )
            return comments
        finally:
            session.close()

    def delete_comment(self, comment_id: int) -> None:
        """Soft delete a comment."""
        session = self.db.get_session()
        try:
            comment = session.query(KanbanComment).filter_by(id=comment_id).first()
            if comment:
                comment.is_deleted = True
                comment.deleted_at = datetime.now()
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Attachment Operations
    # -----------------------------------------------------------------------

    def add_attachment(
        self, task_id: int, file_path: str, file_name: str, file_size: int, mime_type: Optional[str] = None
    ) -> KanbanAttachment:
        """
        Add an attachment to a task.

        Args:
            task_id: Task ID
            file_path: Path to the file
            file_name: Original file name
            file_size: File size in bytes
            mime_type: Optional MIME type

        Returns:
            Created attachment object

        Raises:
            ValueError: If task not found
        """
        session = self.db.get_session()
        try:
            task = session.query(KanbanTask).filter_by(id=task_id, is_deleted=False).first()
            if not task:
                raise ValueError(f"Task {task_id} not found")

            attachment = KanbanAttachment(
                task_id=task_id,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                uploaded_by=self.current_user_id,
            )
            session.add(attachment)
            session.flush()

            # Log attachment addition
            self.logger.log_attachment_added(attachment, self.current_user_id)

            session.commit()
            return attachment

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_attachments(self, task_id: int) -> List[KanbanAttachment]:
        """Get all non-deleted attachments for a task."""
        session = self.db.get_session()
        try:
            attachments = (
                session.query(KanbanAttachment)
                .filter_by(task_id=task_id, is_deleted=False)
                .order_by(KanbanAttachment.uploaded_at)
                .all()
            )
            return attachments
        finally:
            session.close()

    def delete_attachment(self, attachment_id: int, remove_file: bool = True) -> None:
        """
        Soft delete an attachment and optionally remove the file.

        Args:
            attachment_id: Attachment ID
            remove_file: Whether to remove the physical file
        """
        session = self.db.get_session()
        try:
            attachment = session.query(KanbanAttachment).filter_by(id=attachment_id).first()
            if attachment:
                # Remove physical file if requested
                if remove_file and attachment.file_path and os.path.exists(attachment.file_path):
                    try:
                        os.remove(attachment.file_path)
                    except Exception:
                        pass  # File already deleted or permission error

                # Soft delete in database
                attachment.is_deleted = True
                attachment.deleted_at = datetime.now()
                attachment.deleted_by = self.current_user_id

                # Log attachment removal
                self.logger.log_attachment_removed(attachment, self.current_user_id)

                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # User Operations
    # -----------------------------------------------------------------------

    def get_all_users(self) -> List[KanbanUser]:
        """Get all active users."""
        session = self.db.get_session()
        try:
            users = session.query(KanbanUser).filter_by(is_active=True).order_by(KanbanUser.display_name).all()
            return users
        finally:
            session.close()

    def get_user(self, user_id: int) -> Optional[KanbanUser]:
        """Get a user by ID."""
        session = self.db.get_session()
        try:
            user = session.query(KanbanUser).filter_by(id=user_id, is_active=True).first()
            return user
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[KanbanUser]:
        """Get a user by username."""
        session = self.db.get_session()
        try:
            user = session.query(KanbanUser).filter_by(username=username, is_active=True).first()
            return user
        finally:
            session.close()

    # -----------------------------------------------------------------------
    # Utility Methods
    # -----------------------------------------------------------------------

    def _generate_task_number(self, session: Session) -> str:
        """
        Generate a unique task number (TASK-0001, TASK-0002, etc.).

        Args:
            session: Active database session

        Returns:
            Generated task number
        """
        # Get the highest task number
        last_task = session.query(KanbanTask).order_by(KanbanTask.id.desc()).first()

        if last_task and last_task.task_number:
            # Extract number from last task
            try:
                last_num = int(last_task.task_number.split("-")[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                # Fallback to ID-based numbering
                next_num = (last_task.id or 0) + 1
        else:
            next_num = 1

        return f"TASK-{next_num:04d}"

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get overall task statistics."""
        session = self.db.get_session()
        try:
            total_tasks = session.query(KanbanTask).filter_by(is_deleted=False).count()
            completed_tasks = session.query(KanbanTask).filter_by(status="completed", is_deleted=False).count()
            overdue_tasks = (
                session.query(KanbanTask)
                .filter(KanbanTask.deadline < datetime.now().date(), KanbanTask.is_deleted == False)
                .count()
            )

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "overdue_tasks": overdue_tasks,
            }
        finally:
            session.close()

