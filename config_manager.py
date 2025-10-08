"""Configuration management helpers for the IT admin tool."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


CONFIG_FILENAME = "it_tool_config.json"
CONFIG_PATH = Path(__file__).resolve().parent / CONFIG_FILENAME
CONFIG_BACKUP_DIR = Path(__file__).resolve().parent / "config_backups"
CONFIG_CHANGELOG = CONFIG_BACKUP_DIR / "config_changelog.jsonl"

DEFAULT_SIGNATURE = (
    "Best Regards,\n"
    "Seen Ken Yi\n"
    "IT Support Engineer(PM Shift)\n"
    "Ingrasys(Singapore) Pte. Ltd\n"
    "Ext: 63305563\n"
    "Email: kenyi.seen@Ingrasys.com"
)

DEFAULT_CONFIG: Dict[str, Any] = {
    "active_profile": "default",
    "paths": {
        "consolidated_excel": "",
        "new_user_save_folder": "",
        "sap_ticket_image_dir": "",
        "agile_ticket_image_dir": "",
        "singtel_igs32_path": "",
        "singtel_cnt35_path": "",
        "m1_igs32_path": "",
        "m1_cnt35_path": "",
        "m1_igs32_excel": "",
        "m1_cnt35_excel": ""
    },
    "email_settings": {
        "signature": DEFAULT_SIGNATURE,
        "new_user": {
            "to": "benni.yh.tsao@ingrasys.com; rayliao@ingrasys.com",
            "cc": "lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; chinyong.lim@ingrasys.com; oscar.loo@ingrasys.com"
        },
        "disable_user": {
            "to": "benni.yh.tsao@ingrasys.com; rayliao@ingrasys.com",
            "cc": "lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; chinyong.lim@ingrasys.com; oscar.loo@ingrasys.com"
        },
        "sap_support": {
            "to": "kenyi.seen@ingrasys.com",
            "cc": "kenyi.seen@ingrasys.com"
        },
        "sap_creation": {
            "to": "kenyi.seen@ingrasys.com",
            "cc": "kenyi.seen@ingrasys.com"
        },
        "agile_creation": {
            "to": "zhong.yang@fii-foxconn.com",
            "cc": "lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; oscar.loo@ingrasys.com; chinyong.lim@ingrasys.com"
        },
        "agile_reset": {
            "to": "zhong.yang@fii-foxconn.com",
            "cc": "lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; oscar.loo@ingrasys.com; chinyong.lim@ingrasys.com"
        },
        "singtel_telco": {
            "to": "kenyi.seen@ingrasys.com",
            "cc": "kenyi.seen@ingrasys.com"
        },
        "m1_telco": {
            "to": "kenyi.seen@ingrasys.com",
            "cc": "kenyi.seen@ingrasys.com"
        }
    },
    "profiles": {},
}


def _merge_dicts(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def _load_raw_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            data = {}
    else:
        data = {}

    if not isinstance(data, dict):
        data = {}

    data.setdefault("active_profile", "default")
    data.setdefault("profiles", {})
    return data


def _save_raw_config(raw_cfg: Dict[str, Any], *, action: str = "update", metadata: Dict[str, Any] | None = None) -> None:
    CONFIG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_PATH.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        backup_filename = f"it_tool_config_{timestamp}.json"
        backup_path = CONFIG_BACKUP_DIR / backup_filename
        try:
            shutil.copy2(CONFIG_PATH, backup_path)
        except Exception:
            backup_path = None
        else:
            changelog_entry = {
                "timestamp": timestamp,
                "action": action,
                "backup_file": backup_filename,
                "active_profile": raw_cfg.get("active_profile", "default"),
                "metadata": metadata or {},
            }
            with CONFIG_CHANGELOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(changelog_entry, ensure_ascii=False))
                handle.write("\n")

    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(raw_cfg, handle, indent=2)


def get_effective_config(profile: str | None = None, raw_cfg: Dict[str, Any] | None = None) -> Dict[str, Any]:
    raw_cfg = deepcopy(raw_cfg) if raw_cfg is not None else _load_raw_config()
    if profile is None:
        profile = raw_cfg.get("active_profile", "default")

    merged = deepcopy(DEFAULT_CONFIG)
    base_keys = {k: v for k, v in raw_cfg.items() if k not in {"profiles"}}
    _merge_dicts(merged, base_keys)

    if profile != "default":
        profile_cfg = raw_cfg.get("profiles", {}).get(profile, {})
        _merge_dicts(merged, deepcopy(profile_cfg))

    merged["active_profile"] = profile
    merged["available_profiles"] = ["default", *sorted(raw_cfg.get("profiles", {}).keys())]
    return merged


def load_config() -> Dict[str, Any]:
    return get_effective_config()


def save_config(cfg: Dict[str, Any]) -> None:
    _save_raw_config(cfg)


def _target_section(raw_cfg: Dict[str, Any], profile: str, section: str) -> Dict[str, Any]:
    if profile == "default":
        container = raw_cfg.setdefault(section, {})
    else:
        profiles = raw_cfg.setdefault("profiles", {})
        profile_cfg = profiles.setdefault(profile, {})
        container = profile_cfg.setdefault(section, {})
    return container


def get_active_profile_name() -> str:
    raw_cfg = _load_raw_config()
    return raw_cfg.get("active_profile", "default")


def set_active_profile(name: str) -> None:
    raw_cfg = _load_raw_config()
    available = {"default", *raw_cfg.get("profiles", {}).keys()}
    if name not in available:
        raise ValueError(f"Unknown profile '{name}'.")
    raw_cfg["active_profile"] = name
    _save_raw_config(raw_cfg, action="switch_profile", metadata={"profile": name})


def list_profiles() -> List[str]:
    raw_cfg = _load_raw_config()
    return ["default", *sorted(raw_cfg.get("profiles", {}).keys())]


def create_profile(name: str, *, source_profile: str | None = None) -> None:
    safe_name = name.strip()
    if not safe_name:
        raise ValueError("Profile name cannot be empty.")
    if safe_name.lower() == "default":
        raise ValueError("Profile name 'default' is reserved.")

    raw_cfg = _load_raw_config()
    profiles = raw_cfg.setdefault("profiles", {})
    if safe_name in profiles:
        raise ValueError(f"Profile '{safe_name}' already exists.")

    if source_profile is None:
        source_profile = raw_cfg.get("active_profile", "default")

    snapshot = get_effective_config(source_profile, raw_cfg)
    profile_payload = {
        "paths": deepcopy(snapshot.get("paths", {})),
        "email_settings": deepcopy(snapshot.get("email_settings", {})),
    }
    profiles[safe_name] = profile_payload
    raw_cfg.setdefault("active_profile", "default")
    _save_raw_config(raw_cfg, action="create_profile", metadata={"profile": safe_name})


def delete_profile(name: str) -> None:
    raw_cfg = _load_raw_config()
    if name == "default":
        raise ValueError("Cannot delete the default profile.")
    profiles = raw_cfg.get("profiles", {})
    if name not in profiles:
        raise ValueError(f"Profile '{name}' does not exist.")
    profiles.pop(name, None)
    if raw_cfg.get("active_profile") == name:
        raw_cfg["active_profile"] = "default"
    _save_raw_config(raw_cfg, action="delete_profile", metadata={"profile": name})


def list_config_backups(limit: int = 10) -> List[Dict[str, Any]]:
    if not CONFIG_CHANGELOG.exists():
        return []

    with CONFIG_CHANGELOG.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    entries: List[Dict[str, Any]] = []
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        entries.append(entry)
        if len(entries) >= limit:
            break

    return entries


def get_path(key: str, profile: str | None = None) -> str:
    cfg = get_effective_config(profile)
    return cfg.get("paths", {}).get(key, "")


def set_path(key: str, value: str, profile: str | None = None) -> None:
    raw_cfg = _load_raw_config()
    profile = profile or raw_cfg.get("active_profile", "default")
    section = _target_section(raw_cfg, profile, "paths")
    if value:
        section[key] = value
    else:
        section.pop(key, None)
    _save_raw_config(raw_cfg, action="update_paths", metadata={"profile": profile, "key": key})


def list_paths(profile: str | None = None) -> Dict[str, str]:
    cfg = get_effective_config(profile)
    return deepcopy(cfg.get("paths", {}))


def list_email_sections(profile: str | None = None) -> Dict[str, Dict[str, str]]:
    cfg = get_effective_config(profile)
    email_settings = cfg.get("email_settings", {})
    return deepcopy(email_settings)


def get_email_settings(section: str, profile: str | None = None) -> Dict[str, str]:
    cfg = get_effective_config(profile)
    section_data = cfg.get("email_settings", {}).get(section, {})
    return deepcopy(section_data)


def update_email_settings(section: str, settings: Dict[str, str], profile: str | None = None) -> None:
    raw_cfg = _load_raw_config()
    profile = profile or raw_cfg.get("active_profile", "default")
    email_cfg = _target_section(raw_cfg, profile, "email_settings")
    section_cfg = email_cfg.setdefault(section, {})
    section_cfg.update(settings)
    _save_raw_config(raw_cfg, action="update_email_settings", metadata={"profile": profile, "section": section})


def get_signature_text(profile: str | None = None) -> str:
    cfg = get_effective_config(profile)
    signature = cfg.get("email_settings", {}).get("signature", DEFAULT_SIGNATURE)
    if isinstance(signature, (list, tuple)):
        return "\n".join(signature)
    return signature


def set_signature_text(value: str, profile: str | None = None) -> None:
    raw_cfg = _load_raw_config()
    profile = profile or raw_cfg.get("active_profile", "default")
    email_cfg = _target_section(raw_cfg, profile, "email_settings")
    email_cfg["signature"] = value
    _save_raw_config(raw_cfg, action="update_signature", metadata={"profile": profile})


def get_profile_snapshot(profile: str | None = None) -> Dict[str, Any]:
    cfg = get_effective_config(profile)
    return {
        "profile": cfg.get("active_profile", profile or "default"),
        "paths": deepcopy(cfg.get("paths", {})),
        "email_settings": deepcopy(cfg.get("email_settings", {})),
    }


def update_profile_settings(
    profile: str | None = None,
    *,
    paths: Dict[str, str] | None = None,
    email_settings: Dict[str, Dict[str, str]] | None = None,
    signature: str | None = None,
) -> None:
    raw_cfg = _load_raw_config()
    profile_name = profile or raw_cfg.get("active_profile", "default")

    metadata: Dict[str, Any] = {"profile": profile_name}

    if paths is not None:
        target_paths = _target_section(raw_cfg, profile_name, "paths")
        target_paths.update(paths)
        metadata["paths"] = list(paths.keys())

    if email_settings is not None:
        email_cfg = _target_section(raw_cfg, profile_name, "email_settings")
        for section_name, values in email_settings.items():
            section_cfg = email_cfg.setdefault(section_name, {})
            section_cfg.update(values)
        metadata["email_sections"] = list(email_settings.keys())

    if signature is not None:
        email_cfg = _target_section(raw_cfg, profile_name, "email_settings")
        email_cfg["signature"] = signature
        metadata["signature"] = True

    _save_raw_config(raw_cfg, action="update_profile", metadata=metadata)

