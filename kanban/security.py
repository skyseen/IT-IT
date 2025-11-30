"""Security helpers for Kanban authentication."""

from __future__ import annotations

import secrets
import string
from typing import Tuple

import bcrypt


PASSWORD_MIN_LENGTH = 8


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str | None) -> bool:
    """Verify a plaintext password against a hashed password."""

    if not password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def generate_session_token() -> str:
    """Generate a random session token."""

    return secrets.token_urlsafe(48)


def generate_temporary_password(length: int = 12) -> str:
    """Generate a temporary password with reasonable complexity."""

    if length < PASSWORD_MIN_LENGTH:
        length = PASSWORD_MIN_LENGTH

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(password: str) -> Tuple[bool, str | None]:
    """Validate password strength and return (is_valid, error_message)."""

    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."

    if password.lower() == password or password.upper() == password:
        return False, "Password must contain both uppercase and lowercase letters."

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit."

    if not any(char in "!@#$%^&*()-_=+" for char in password):
        return False, "Password must contain at least one special character (e.g. !@#$)."

    return True, None













