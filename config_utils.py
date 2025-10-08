import json
import os
from copy import deepcopy


CONFIG_FILENAME = "sap_tool_config.json"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)

DEFAULT_SIGNATURE = (
    "Best Regards,\n"
    "Seen Ken Yi\n"
    "IT Support Engineer(PM Shift)\n"
    "Ingrasys(Singapore) Pte. Ltd\n"
    "Ext: 63305563\n"
    "Email: kenyi.seen@Ingrasys.com"
)

DEFAULT_CONFIG = {
    "paths": {
        "consolidated_excel": "",
        "new_user_save_folder": "C:/Users/Shared/IT/NewUser" ,
        "sap_ticket_image_dir": ""
    },
    "email": {
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
        }
    }
}


def _merge_dicts(base, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dicts(base[key], value)
        else:
            base[key] = value


def load_config():
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


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_email_settings(section):
    cfg = load_config()
    return cfg.get("email", {}).get(section, {})


def get_signature_text():
    cfg = load_config()
    return cfg.get("email", {}).get("signature", DEFAULT_SIGNATURE)


def get_signature_html():
    return "<br>".join(get_signature_text().splitlines())


def get_path(key):
    cfg = load_config()
    return cfg.get("paths", {}).get(key, "")


def update_config_path(key, value):
    cfg = load_config()
    cfg.setdefault("paths", {})[key] = value
    save_config(cfg)


def update_email_settings(section, data):
    cfg = load_config()
    email_cfg = cfg.setdefault("email", {})
    section_cfg = email_cfg.setdefault(section, {})
    _merge_dicts(section_cfg, data)
    save_config(cfg)


