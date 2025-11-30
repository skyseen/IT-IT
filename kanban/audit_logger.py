"""Audit logging wrapper for Kanban operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from activity_log import log_event


class AuditLogger:
    """
    Wrapper for audit logging in Kanban system.
    Logs to both PostgreSQL (detailed) and JSONL (summary).
    """

    def __init__(self, db_manager):
        """
        Initialize audit logger.

        Args:
            db_manager: Database manager instance for PostgreSQL logging
        """
        self.db_manager = db_manager

    def log_activity(
        self,
        activity_type: str,
        user_id: int,
        task_id: Optional[int] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        comment: Optional[str] = None,
        task_snapshot: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log an activity to both PostgreSQL and JSONL.

        Args:
            activity_type: Type of activity (e.g., 'task_created', 'task_moved')
            user_id: ID of user performing the action
            task_id: Optional task ID related to the activity
            field_name: Optional field name that changed
            old_value: Optional old value before change
            new_value: Optional new value after change
            comment: Optional comment or additional context
            task_snapshot: Optional complete task state snapshot
            ip_address: Optional user's IP address
            user_agent: Optional user agent string
        """
        from kanban.models import KanbanActivityLog

        print(f"[AuditLog] log_activity called: type={activity_type}, field={field_name}, old={old_value}, new={new_value}")

        # Log to PostgreSQL (detailed)
        session = self.db_manager.get_session()
        try:
            activity_log = KanbanActivityLog(
                task_id=task_id,
                activity_type=activity_type,
                user_id=user_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                comment=comment,
                task_snapshot=task_snapshot,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(activity_log)
            session.commit()
            print(f"[AuditLog] Activity logged to DB: id={activity_log.id}")
        except Exception as e:
            session.rollback()
            # Log error but don't fail the operation
            log_event(
                "kanban.audit",
                f"Failed to log activity to database: {e}",
                level="error",
                details={
                    "activity_type": activity_type,
                    "task_id": task_id,
                    "user_id": user_id,
                },
            )
        finally:
            session.close()

        # Log to JSONL (summary via existing activity_log)
        self._log_to_jsonl(
            activity_type=activity_type,
            user_id=user_id,
            task_id=task_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            comment=comment,
        )

    def _log_to_jsonl(
        self,
        activity_type: str,
        user_id: int,
        task_id: Optional[int] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Log summary to JSONL via existing activity_log module."""
        # Build human-readable message
        message = self._format_activity_message(
            activity_type=activity_type,
            task_id=task_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            comment=comment,
        )

        # Build details dictionary
        details: Dict[str, Any] = {
            "activity_type": activity_type,
            "user_id": user_id,
        }

        if task_id is not None:
            details["task_id"] = task_id
        if field_name:
            details["field_name"] = field_name
        if old_value:
            details["old_value"] = old_value
        if new_value:
            details["new_value"] = new_value
        if comment:
            details["comment"] = comment

        # Log to existing activity_log.jsonl
        log_event("kanban", message, level="info", details=details)

    def _format_activity_message(
        self,
        activity_type: str,
        task_id: Optional[int] = None,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> str:
        """Format a human-readable activity message."""
        task_ref = f"Task #{task_id}" if task_id else "Task"

        if activity_type == "task_created":
            return f"{task_ref} created"
        elif activity_type == "task_updated":
            if field_name:
                return f"{task_ref} updated: {field_name} changed from '{old_value}' to '{new_value}'"
            return f"{task_ref} updated"
        elif activity_type == "task_deleted":
            return f"{task_ref} deleted"
        elif activity_type == "task_moved":
            return f"{task_ref} moved from column {old_value} to {new_value}"
        elif activity_type == "task_assigned":
            return f"{task_ref} assigned to user {new_value}"
        elif activity_type == "task_unassigned":
            return f"{task_ref} unassigned from user {old_value}"
        elif activity_type == "priority_changed":
            return f"{task_ref} priority changed from {old_value} to {new_value}"
        elif activity_type == "deadline_changed":
            return f"{task_ref} deadline changed from {old_value} to {new_value}"
        elif activity_type == "comment_added":
            return f"Comment added to {task_ref}"
        elif activity_type == "attachment_added":
            return f"Attachment added to {task_ref}: {comment}"
        elif activity_type == "attachment_removed":
            return f"Attachment removed from {task_ref}: {comment}"
        else:
            return f"{task_ref} - {activity_type}"

    def log_task_created(self, task, user_id: int) -> None:
        """Log task creation."""
        self.log_activity(
            activity_type="task_created",
            user_id=user_id,
            task_id=task.id,
            new_value=task.title,
            task_snapshot=self._task_to_dict(task),
        )

    def log_task_updated(
        self, task, user_id: int, changes: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Log task updates.

        Args:
            task: Task object
            user_id: User ID
            changes: Dictionary of changes {field_name: {'old': old_val, 'new': new_val}}
        """
        for field_name, change in changes.items():
            self.log_activity(
                activity_type="task_updated",
                user_id=user_id,
                task_id=task.id,
                field_name=field_name,
                old_value=str(change.get("old", "")),
                new_value=str(change.get("new", "")),
            )

    def log_task_deleted(self, task, user_id: int) -> None:
        """Log task deletion."""
        self.log_activity(
            activity_type="task_deleted",
            user_id=user_id,
            task_id=task.id,
            old_value=task.title,
            task_snapshot=self._task_to_dict(task),
        )

    def log_task_moved(self, task, user_id: int, old_column_id: int, new_column_id: int) -> None:
        """Log task move between columns."""
        from kanban.models import KanbanColumn
        
        # Get column names instead of IDs for better readability
        session = self.db_manager.get_session()
        try:
            old_column = session.query(KanbanColumn).filter_by(id=old_column_id).first()
            new_column = session.query(KanbanColumn).filter_by(id=new_column_id).first()
            
            old_column_name = old_column.name if old_column else f"Column #{old_column_id}"
            new_column_name = new_column.name if new_column else f"Column #{new_column_id}"
            
            print(f"[AuditLog] Logging move: FROM '{old_column_name}' TO '{new_column_name}'")
        finally:
            session.close()
        
        self.log_activity(
            activity_type="task_moved",
            user_id=user_id,
            task_id=task.id,
            field_name="column",
            old_value=old_column_name,
            new_value=new_column_name,
        )

    def log_comment_added(self, comment, user_id: int) -> None:
        """Log comment addition."""
        self.log_activity(
            activity_type="comment_added",
            user_id=user_id,
            task_id=comment.task_id,
            comment=comment.comment[:100] + "..." if len(comment.comment) > 100 else comment.comment,
        )

    def log_attachment_added(self, attachment, user_id: int) -> None:
        """Log attachment addition."""
        self.log_activity(
            activity_type="attachment_added",
            user_id=user_id,
            task_id=attachment.task_id,
            comment=attachment.file_name,
        )

    def log_attachment_removed(self, attachment, user_id: int) -> None:
        """Log attachment removal."""
        self.log_activity(
            activity_type="attachment_removed",
            user_id=user_id,
            task_id=attachment.task_id,
            comment=attachment.file_name,
        )

    @staticmethod
    def _task_to_dict(task) -> Dict[str, Any]:
        """Convert task object to dictionary for snapshot."""
        return {
            "id": task.id,
            "task_number": task.task_number,
            "title": task.title,
            "description": task.description,
            "column_id": task.column_id,
            "position": float(task.position) if task.position else None,
            "assigned_to": task.assigned_to,
            "created_by": task.created_by,
            "priority": task.priority,
            "status": task.status,
            "category": task.category,
            "tags": task.tags,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "estimated_hours": float(task.estimated_hours) if task.estimated_hours else None,
            "actual_hours": float(task.actual_hours) if task.actual_hours else None,
            "is_workflow_task": task.is_workflow_task,
            "workflow_type": task.workflow_type,
            "workflow_reference": task.workflow_reference,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }


