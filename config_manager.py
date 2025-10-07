"""Configuration management helpers for the IT admin tool."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Dict


CONFIG_FILENAME = "it_tool_config.json"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)

DEFAULT_SIGNATURE = (
    "Best Regards,\n"
    "Seen Ken Yi\n"
    "IT Support Engineer(PM Shift)\n"
    "Ingrasys(Singapore) Pte. Ltd\n"
    "Ext: 63305563\n"
    "Email: kenyi.seen@Ingrasys.com"
)

DEFAULT_CONFIG: Dict[str, Any] = {
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
    }
}


def _merge_dicts(base: Dict[str, Any], updates: Dict[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
        except Exception:
            stored = {}
    else:
        stored = {}

    merged = deepcopy(DEFAULT_CONFIG)
    _merge_dicts(merged, stored)
    return merged


def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_path(key: str) -> str:
    cfg = load_config()
    return cfg.get("paths", {}).get(key, "")


def set_path(key: str, value: str) -> None:
    cfg = load_config()
    cfg.setdefault("paths", {})[key] = value
    save_config(cfg)


def list_paths() -> Dict[str, str]:
    cfg = load_config()
    return cfg.get("paths", {}).copy()


def list_email_sections() -> Dict[str, Dict[str, str]]:
    cfg = load_config()
    return cfg.get("email_settings", {}).copy()


def get_email_settings(section: str) -> Dict[str, str]:
    cfg = load_config()
    return cfg.get("email_settings", {}).get(section, {})


def update_email_settings(section: str, settings: Dict[str, str]) -> None:
    cfg = load_config()
    email_cfg = cfg.setdefault("email_settings", {})
    section_cfg = email_cfg.setdefault(section, {})
    section_cfg.update(settings)
    save_config(cfg)


def get_signature_text() -> str:
    cfg = load_config()
    return cfg.get("email_settings", {}).get("signature", DEFAULT_SIGNATURE)


def set_signature_text(value: str) -> None:
    cfg = load_config()
    cfg.setdefault("email_settings", {})["signature"] = value
    save_config(cfg)

