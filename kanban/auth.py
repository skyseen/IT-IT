"""Authentication and session management for the Kanban module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from activity_log import log_event

from kanban.database import DatabaseManager, get_db_manager
from kanban.models import KanbanSession, KanbanUser
from kanban.security import (
    generate_session_token,
    generate_temporary_password,
    hash_password,
    validate_password_strength,
    verify_password,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthorizationError(Exception):
    """Raised when a user is not authorized to perform an action."""


@dataclass
class AuthResult:
    """Represents result of a successful authentication."""

    user: KanbanUser
    session: KanbanSession
    remember_me: bool
    must_change_password: bool


def _get_db(db_manager: DatabaseManager | None = None) -> DatabaseManager:
    return db_manager or get_db_manager()


def authenticate(  # noqa: C901 - keep logic together
    username: str,
    password: str,
    *,
    remember_me: bool = False,
    ip_address: str | None = None,
    user_agent: str | None = None,
    db_manager: DatabaseManager | None = None,
) -> AuthResult:
    """Authenticate a user and create a session.

    Raises AuthenticationError on failure.
    """

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        user = (
            session.query(KanbanUser)
            .filter(KanbanUser.username == username, KanbanUser.is_active == True)  # noqa: E712
            .first()
        )
        if not user or not user.password_hash:
            raise AuthenticationError("Invalid username or password.")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")

        # Deactivate existing active sessions for remember_me accounts to avoid duplicates
        session.query(KanbanSession).filter(
            KanbanSession.user_id == user.id,
            KanbanSession.is_active == True,  # noqa: E712
            KanbanSession.remember_me == False,
        ).update({KanbanSession.is_active: False, KanbanSession.logout_at: datetime.now()})

        token = generate_session_token()
        new_session = KanbanSession(
            user_id=user.id,
            session_token=token,
            remember_me=remember_me,
            ip_address=ip_address,
            user_agent=user_agent,
            login_at=datetime.now(),
            last_activity=datetime.now(),
        )
        session.add(new_session)
        user.last_login = datetime.now()
        session.commit()

        log_event(
            "kanban.auth",
            "User authenticated",
            details={"username": user.username, "remember_me": remember_me},
        )

        must_change = bool(user.password_reset_required)
        return AuthResult(user=user, session=new_session, remember_me=remember_me, must_change_password=must_change)
    except AuthenticationError:
        session.rollback()
        raise
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        log_event("kanban.auth", "Authentication failed", level="error", details={"error": str(exc)})
        raise AuthenticationError("Authentication failed due to internal error.") from exc
    finally:
        session.close()


def resume_session(
    token: str,
    *,
    db_manager: DatabaseManager | None = None,
) -> Optional[AuthResult]:
    """Resume an existing session token, returning AuthResult or None if invalid."""

    if not token:
        return None

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        kanban_session = (
            session.query(KanbanSession)
            .filter(
                KanbanSession.session_token == token,
                KanbanSession.is_active == True,  # noqa: E712
            )
            .first()
        )
        if not kanban_session:
            return None

        user = session.query(KanbanUser).filter(KanbanUser.id == kanban_session.user_id, KanbanUser.is_active == True).first()  # noqa: E712
        if not user:
            return None

        kanban_session.last_activity = datetime.now()
        session.commit()

        return AuthResult(
            user=user,
            session=kanban_session,
            remember_me=bool(kanban_session.remember_me),
            must_change_password=bool(user.password_reset_required),
        )
    finally:
        session.close()


def logout(session_token: str, *, db_manager: DatabaseManager | None = None) -> None:
    """Mark a session as logged out."""

    if not session_token:
        return

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        updated = (
            session.query(KanbanSession)
            .filter(KanbanSession.session_token == session_token, KanbanSession.is_active == True)  # noqa: E712
            .update({KanbanSession.is_active: False, KanbanSession.logout_at: datetime.now()})
        )
        if updated:
            session.commit()
            log_event("kanban.auth", "User logged out", details={"session_token": session_token})
        else:
            session.rollback()
    finally:
        session.close()


def update_last_activity(session_token: str, *, db_manager: DatabaseManager | None = None) -> None:
    """Update the last activity timestamp for a session."""

    if not session_token:
        return

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        session.query(KanbanSession).filter(
            KanbanSession.session_token == session_token,
            KanbanSession.is_active == True,  # noqa: E712
        ).update({KanbanSession.last_activity: datetime.now()})
        session.commit()
    finally:
        session.close()


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    *,
    db_manager: DatabaseManager | None = None,
) -> None:
    """Change password for the specified user after verifying the current password."""

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        user = (
            session.query(KanbanUser)
            .filter(KanbanUser.id == user_id, KanbanUser.is_active == True)  # noqa: E712
            .first()
        )
        if not user or not user.password_hash:
            raise AuthenticationError("User account not found.")

        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect.")

        valid, message = validate_password_strength(new_password)
        if not valid:
            raise AuthenticationError(message or "Password does not meet requirements.")

        user.password_hash = hash_password(new_password)
        user.password_last_changed = datetime.now()
        user.password_reset_required = False
        session.commit()

        log_event("kanban.auth", "User changed password", details={"user_id": user.id})
    except AuthenticationError:
        session.rollback()
        raise
    finally:
        session.close()


def admin_reset_password(
    admin_user: KanbanUser,
    target_user_id: int,
    *,
    new_password: Optional[str] = None,
    force_reset: bool = True,
    db_manager: DatabaseManager | None = None,
) -> str:
    """Reset another user's password, returning the new plaintext password."""

    if admin_user.role not in {"admin", "manager"}:
        raise AuthorizationError("You do not have permission to reset passwords.")

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        user = session.query(KanbanUser).filter(KanbanUser.id == target_user_id, KanbanUser.is_active == True).first()  # noqa: E712
        if not user:
            raise AuthenticationError("Target user not found or inactive.")

        password = new_password or generate_temporary_password()
        valid, message = validate_password_strength(password)
        if not valid:
            raise AuthenticationError(message or "Password does not meet requirements.")

        user.password_hash = hash_password(password)
        user.password_last_changed = datetime.now()
        user.password_reset_required = force_reset

        # Invalidate existing sessions
        session.query(KanbanSession).filter(
            KanbanSession.user_id == user.id,
            KanbanSession.is_active == True,  # noqa: E712
        ).update({KanbanSession.is_active: False, KanbanSession.logout_at: datetime.now()})

        session.commit()

        log_event(
            "kanban.auth",
            "Admin reset user password",
            details={"admin": admin_user.username, "target": user.username, "force_reset": force_reset},
        )

        return password
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ensure_password_initialized(
    user: KanbanUser,
    *,
    default_password: str = "ChangeMe123!",
    db_manager: DatabaseManager | None = None,
) -> None:
    """Ensure a user has a password hash set (used by seed scripts)."""

    if user.password_hash:
        return

    db = _get_db(db_manager)
    session = db.get_session()
    try:
        persistent_user = session.query(KanbanUser).filter(KanbanUser.id == user.id).first()
        if persistent_user and not persistent_user.password_hash:
            persistent_user.password_hash = hash_password(default_password)
            persistent_user.password_last_changed = datetime.now()
            persistent_user.password_reset_required = True
            session.commit()
    finally:
        session.close()













