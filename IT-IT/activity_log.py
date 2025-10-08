"""Activity and audit logging utilities for the IT-IT toolkit."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List


_LOG_DIR = Path(__file__).resolve().parent / "logs"
_LOG_FILE = _LOG_DIR / "activity_log.jsonl"
_LISTENERS: List[Callable[[Dict[str, Any]], None]] = []
_LOCK = threading.Lock()


def register_listener(callback: Callable[[Dict[str, Any]], None]) -> None:
    """Register a callback that receives activity events as they are logged."""

    if callback not in _LISTENERS:
        _LISTENERS.append(callback)


def clear_listeners() -> None:
    """Remove all registered listeners. Intended for tests."""

    _LISTENERS.clear()


def log_event(
    category: str,
    message: str,
    *,
    level: str = "info",
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Persist an activity log entry and dispatch it to listeners.

    Parameters
    ----------
    category:
        High level grouping for the event (e.g. ``"user"`` or ``"config"``).
    message:
        Human readable summary of the action that occurred.
    level:
        Severity level. Supported values include ``"info"``, ``"warning"``,
        and ``"error"``.
    details:
        Optional structured metadata that will be serialised with the entry.

    Returns
    -------
    dict
        The entry that was persisted.
    """

    entry = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "category": category,
        "message": message,
        "level": level,
        "details": details or {},
    }

    with _LOCK:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False))
            handle.write("\n")

    for callback in list(_LISTENERS):
        try:
            callback(entry)
        except Exception:
            # Listener failures should not disrupt the automation flows.
            continue

    return entry


def get_recent_events(limit: int = 200) -> List[Dict[str, Any]]:
    """Return the latest activity log entries (most recent last)."""

    if not _LOG_FILE.exists():
        return []

    with _LOG_FILE.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    events: List[Dict[str, Any]] = []
    for raw in lines[-limit:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            events.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    return events


def describe_event(entry: Dict[str, Any]) -> str:
    """Create a short human readable string for the given entry."""

    timestamp = entry.get("timestamp", "")
    level = entry.get("level", "info").upper()
    category = entry.get("category", "general")
    message = entry.get("message", "")
    return f"[{timestamp}] ({level}) {category}: {message}"

