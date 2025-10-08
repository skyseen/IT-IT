"""User workflow helpers for excel generation and queue management."""

from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd


USER_TEMPLATE_COLUMNS: List[str] = [
    "User Name",
    "First Name",
    "Last Name",
    "Display Name",
    "Job Title",
    "Department",
    "Office(Cost Code)",
    "Office Phone",
    "Mobile Phone",
    "Fax",
    "Address",
    "Employee ID",
    "Chinese name",
    "State or Province",
    "Country or Region",
]


def _default_row_from_user(user_data: Dict[str, str]) -> List[str]:
    """Map user form data into the excel template order."""

    return [
        user_data.get("User Name", ""),
        user_data.get("First Name", ""),
        user_data.get("Last Name", ""),
        user_data.get("Display Name", ""),
        user_data.get("Job Title", ""),
        user_data.get("Department", ""),
        "771VBS0005",
        "",
        "",
        "",
        "Singapore",
        user_data.get("Employee ID", ""),
        "",
        "Singapore",
        "Singapore",
    ]


def ensure_directory(path: str) -> None:
    """Create directory if it does not exist (no error if it already exists)."""

    if path:
        os.makedirs(path, exist_ok=True)


def create_user_workbook(user_data: Dict[str, str], save_folder: str) -> str:
    """Generate the single-user excel workbook and return the saved path."""

    ensure_directory(save_folder)
    file_name = f"{user_data.get('Display Name', user_data.get('User Name', 'user'))}.xlsx"
    save_path = os.path.join(save_folder, file_name)

    df = pd.DataFrame([_default_row_from_user(user_data)], columns=USER_TEMPLATE_COLUMNS)
    df.to_excel(save_path, index=False, engine="openpyxl")
    return save_path


def generate_user_workbooks(user_list: List[Dict[str, str]], save_folder: str) -> List[str]:
    """Create excel files for each queued user and return attachment paths."""

    attachments: List[str] = []
    for user_data in user_list:
        attachments.append(create_user_workbook(user_data, save_folder))
    return attachments


