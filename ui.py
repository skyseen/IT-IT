"""PySide6 UI components for the IT admin tool with a dark tech theme."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List

import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets

from activity_log import log_event
from config_manager import (
    create_profile,
    delete_profile,
    get_active_profile_name,
    get_email_settings,
    get_path,
    get_signature_text,
    list_config_backups,
    list_email_sections,
    list_paths,
    list_profiles,
    set_active_profile,
    set_path,
    update_profile_settings,
)
from email_service import (
    send_agile_creation_email,
    send_agile_reset_email,
    send_disable_user_email,
    send_new_user_email,
    send_sap_disable_email,
    send_sap_support_email,
    send_singtel_telco_email,
    send_m1_telco_email,
)
from sap_workflows import (
    build_preview_window,
    disable_sap_accounts,
    get_all_existing_employees,
    parse_user_excel,
)
from telco_workflows import (
    process_m1_bill,
    process_singtel_bills,
    update_both_m1_excels,
)
from user_workflow import generate_user_workbooks

# ---------------------------------------------------------------------------
# Dark tech palette
# ---------------------------------------------------------------------------

BASE_BG = "#0F172A"
SURFACE_BG = "#111C2E"
CARD_BG = "#14243B"
ELEVATED_BG = "#1E2E46"
ACCENT = "#38BDF8"
ACCENT_SOFT = "#1D4ED8"
SUCCESS = "#34D399"
WARNING = "#FBBF24"
DANGER = "#F87171"
INFO = "#60A5FA"
TEXT_PRIMARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#1F3A5F"
GLOSS = "#1B2840"


def _active_parent(parent: QtWidgets.QWidget | None = None) -> QtWidgets.QWidget | None:
    return parent or QtWidgets.QApplication.activeWindow()


def show_error(message: str, title: str = "Error", parent: QtWidgets.QWidget | None = None) -> None:
    QtWidgets.QMessageBox.critical(_active_parent(parent), title, message)


def show_warning(message: str, title: str = "Warning", parent: QtWidgets.QWidget | None = None) -> None:
    QtWidgets.QMessageBox.warning(_active_parent(parent), title, message)


def show_info(message: str, title: str = "Information", parent: QtWidgets.QWidget | None = None) -> None:
    QtWidgets.QMessageBox.information(_active_parent(parent), title, message)


def ask_yes_no(message: str, title: str = "Confirm", parent: QtWidgets.QWidget | None = None) -> bool:
    response = QtWidgets.QMessageBox.question(
        _active_parent(parent), title, message, QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
    )
    return response == QtWidgets.QMessageBox.StandardButton.Yes


def get_open_file(
    title: str,
    filters: str,
    parent: QtWidgets.QWidget | None = None,
    directory: str | None = None,
) -> str:
    dialog_parent = _active_parent(parent)
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(dialog_parent, title, directory or "", filters)
    return file_path


def get_existing_directory(title: str, parent: QtWidgets.QWidget | None = None, directory: str | None = None) -> str:
    return QtWidgets.QFileDialog.getExistingDirectory(_active_parent(parent), title, directory or "")


def apply_dark_tech_palette(app: QtWidgets.QApplication) -> None:
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(BASE_BG))
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(TEXT_PRIMARY))
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(SURFACE_BG))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(CARD_BG))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(ELEVATED_BG))
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(TEXT_PRIMARY))
    palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(TEXT_PRIMARY))
    palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(CARD_BG))
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(TEXT_PRIMARY))
    palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(ACCENT))
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(BASE_BG))
    app.setPalette(palette)

    base_stylesheet = f"""
        QWidget {{
            color: {TEXT_PRIMARY};
            background-color: {BASE_BG};
            font-family: 'Segoe UI', 'Inter', 'Arial';
        }}
        QGroupBox {{
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            margin-top: 18px;
            background-color: {CARD_BG};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 20px;
            padding: 0 8px;
            font-size: 13px;
            color: {ACCENT};
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        QPushButton {{
            background-color: {ACCENT};
            color: #09111F;
            border-radius: 8px;
            padding: 12px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {INFO};
        }}
        QPushButton:pressed {{
            background-color: {ACCENT_SOFT};
        }}
        QListWidget, QTreeWidget, QTextEdit, QLineEdit, QPlainTextEdit {{
            background-color: {SURFACE_BG};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
        }}
        QTabWidget::pane {{
            border: 1px solid {BORDER_COLOR};
            border-radius: 14px;
            padding: 6px;
            background-color: {CARD_BG};
        }}
        QTabBar::tab {{
            background-color: transparent;
            padding: 10px 18px;
            margin: 2px;
            border-radius: 10px;
            color: {TEXT_MUTED};
            font-weight: 600;
        }}
        QTabBar::tab:selected {{
            background-color: {ACCENT_SOFT};
            color: {TEXT_PRIMARY};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 0px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: transparent;
            border-radius: 0px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background: none;
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 0px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: transparent;
        }}
        QLabel[role='caption'] {{
            color: {TEXT_MUTED};
            font-size: 11px;
            letter-spacing: 0.06em;
        }}
    """
    app.setStyleSheet(base_stylesheet)


# ---------------------------------------------------------------------------
# Action cards used on the dashboard
# ---------------------------------------------------------------------------


@dataclass
class Action:
    title: str
    description: str
    handler: Callable[[QtWidgets.QWidget], None]
    accent: str = ACCENT
    icon: str | None = None


class ActionCard(QtWidgets.QFrame):
    def __init__(self, action: Action, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.action = action
        self.setObjectName("actionCard")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(180)
        self.setStyleSheet(
            f"""
            QFrame#actionCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {CARD_BG},
                    stop:1 rgba(15, 23, 42, 0.85));
                border: 2px solid {BORDER_COLOR};
                border-radius: 18px;
                padding: 4px;
            }}
            QFrame#actionCard:hover {{
                border-color: {action.accent};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.95),
                    stop:1 rgba(20, 30, 48, 0.95));
            }}
        """
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(16)
        if action.icon:
            icon_label = QtWidgets.QLabel(action.icon)
            icon_label.setStyleSheet("font-size: 40px;")
            header.addWidget(icon_label)
        title = QtWidgets.QLabel(action.title)
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY}; letter-spacing: 0.01em;"
        )
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        description = QtWidgets.QLabel(action.description)
        description.setWordWrap(True)
        description.setMinimumHeight(40)
        description.setStyleSheet(f"color: {TEXT_MUTED}; line-height: 1.8; font-size: 14px;")
        layout.addWidget(description)

        launch_button = QtWidgets.QPushButton("▶ Launch Workflow")
        launch_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        launch_button.setMinimumHeight(48)
        launch_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {action.accent};
                color: #051221;
                font-weight: 700;
                font-size: 15px;
                padding: 14px 24px;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {ACCENT};
                padding: 15px 23px 13px 25px;
            }}
            """
        )
        launch_button.clicked.connect(lambda: action.handler(self))
        layout.addWidget(launch_button)
        
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Make the entire card clickable"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.action.handler(self)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# Dialog utilities
# ---------------------------------------------------------------------------


class MultiUserDialog(QtWidgets.QDialog):
    def __init__(
        self,
        title: str,
        labels: Iterable[str],
        submit_handler: Callable[[List[Dict[str, str]]], None],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(760, 560)
        self.setModal(True)
        self.labels = list(labels)
        self.submit_handler = submit_handler
        self.user_rows: List[Dict[str, str]] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        header = QtWidgets.QLabel(
            "Organize your batch run. Fields support special characters and will be validated before submission."
        )
        header.setWordWrap(True)
        header.setProperty("role", "caption")
        layout.addWidget(header)

        form_grid = QtWidgets.QGridLayout()
        form_grid.setVerticalSpacing(12)
        form_grid.setHorizontalSpacing(16)
        self.inputs: Dict[str, QtWidgets.QLineEdit] = {}
        for idx, label in enumerate(self.labels):
            lbl = QtWidgets.QLabel(label)
            lbl.setStyleSheet("font-weight: 600;")
            field = QtWidgets.QLineEdit()
            field.setPlaceholderText(f"Enter {label.lower()}")
            self.inputs[label] = field
            form_grid.addWidget(lbl, idx, 0)
            form_grid.addWidget(field, idx, 1)
        form_grid.setColumnStretch(1, 1)
        layout.addLayout(form_grid)

        list_group = QtWidgets.QGroupBox("User Queue")
        list_layout = QtWidgets.QVBoxLayout(list_group)
        list_layout.setContentsMargins(16, 16, 16, 16)
        list_layout.setSpacing(10)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        list_layout.addWidget(self.list_widget)

        button_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add User")
        add_btn.setStyleSheet(f"background-color: {SUCCESS}; color: #051221;")
        remove_btn = QtWidgets.QPushButton("Remove Selected")
        remove_btn.setStyleSheet(f"background-color: {DANGER}; color: #051221;")
        add_btn.clicked.connect(self.add_user)
        remove_btn.clicked.connect(self.remove_user)
        button_row.addWidget(add_btn)
        button_row.addWidget(remove_btn)
        list_layout.addLayout(button_row)
        layout.addWidget(list_group, 1)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Run Workflow")
        submit_btn.setStyleSheet(f"background-color: {ACCENT}; color: #051221; font-weight: 700;")
        submit_btn.clicked.connect(self.submit)
        footer.addWidget(cancel_btn)
        footer.addWidget(submit_btn)
        layout.addLayout(footer)

    def add_user(self) -> None:
        data = {label: field.text().strip() for label, field in self.inputs.items()}
        if not all(data.values()):
            show_error("All fields must be filled before adding a user.", parent=self)
            return
        self.user_rows.append(data)
        self._refresh()
        for field in self.inputs.values():
            field.clear()
        first_field = self.inputs[self.labels[0]]
        first_field.setFocus()

    def remove_user(self) -> None:
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            show_warning("Select a user in the queue to remove.", parent=self)
            return
        self.user_rows.pop(current_row)
        self._refresh()

    def submit(self) -> None:
        if not self.user_rows:
            show_error("Add at least one user before submitting.", parent=self)
            return
        if not ask_yes_no(
            f"Execute batch operation for {len(self.user_rows)} user(s)?\nThis action cannot be undone.",
            title="Confirm Batch",
            parent=self,
        ):
            return
        self.submit_handler(self.user_rows)
        self.accept()

    def _refresh(self) -> None:
        self.list_widget.clear()
        for idx, data in enumerate(self.user_rows, start=1):
            primary = data.get(self.labels[0], "")
            display = data.get("Display Name") or data.get("User Name") or ""
            self.list_widget.addItem(f"{idx:02d} • {primary} → {display}")


# ---------------------------------------------------------------------------
# Workflow handlers (business logic with Qt dialogs)
# ---------------------------------------------------------------------------


def handle_new_user_email(user_list: List[Dict[str, str]]) -> None:
    log_event("user.onboarding", "Preparing new user onboarding email run", details={"count": len(user_list)})

    parent = QtWidgets.QApplication.activeWindow()
    save_folder = get_path("new_user_save_folder")
    if not save_folder:
        selected = get_existing_directory("Select folder to save new user templates", parent=parent)
        if not selected:
            show_error("Save folder is required to generate templates.", parent=parent)
            log_event(
                "user.onboarding",
                "New user email workflow cancelled - missing save folder",
                level="warning",
            )
            return
        set_path("new_user_save_folder", selected)
        save_folder = selected

    try:
        attachments = generate_user_workbooks(user_list, save_folder)
        send_new_user_email(user_list, attachments)
    except Exception as exc:  # noqa: BLE001
        log_event(
            "user.onboarding",
            "New user email workflow failed",
            level="error",
            details={"error": str(exc)},
        )
        show_error(f"Unable to prepare and send the new user email.\n\nDetails: {exc}", parent=parent)
        return

    log_event(
        "user.onboarding",
        "New user email dispatched",
        details={"count": len(user_list), "attachments": len(attachments)},
    )
    show_info(f"New user email sent with {len(attachments)} attachments.", title="Success", parent=parent)


def handle_disable_user_email(user_list: List[Dict[str, str]]) -> None:
    parent = QtWidgets.QApplication.activeWindow()
    try:
        send_disable_user_email(user_list)
    except Exception as exc:  # noqa: BLE001
        log_event(
            "user.offboarding",
            "Disable user email workflow failed",
            level="error",
            details={"error": str(exc), "count": len(user_list)},
        )
        show_error(
            f"Unable to complete disable user email workflow.\n\nDetails: {exc}",
            parent=parent,
        )
        return

    log_event("user.offboarding", "Disable user email dispatched", details={"count": len(user_list)})
    show_info("Disable user email sent successfully.", title="Success", parent=parent)


# ---------------------------------------------------------------------------
# SAP workflows
# ---------------------------------------------------------------------------


def launch_sap_flow(parent: QtWidgets.QWidget | None = None) -> None:
    user_excel_path = get_open_file(
        "Select user-submitted SAP Excel",
        "Excel files (*.xlsx *.xls);;All files (*.*)",
        parent=parent,
    )
    if not user_excel_path:
        log_event("sap.creation", "SAP creation flow cancelled - no Excel selected", level="warning")
        return

    # Create progress dialog to show loading status
    progress = QtWidgets.QProgressDialog("Reading Excel file...", None, 0, 0, parent)
    progress.setWindowTitle("Loading")
    progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    QtWidgets.QApplication.processEvents()

    try:
        # Check if file exists and is accessible
        if not os.path.exists(user_excel_path):
            progress.close()
            show_error(f"File not found:\n{user_excel_path}", parent=parent)
            return
        
        # Check if file is locked (opened in Excel)
        try:
            with open(user_excel_path, 'r+b'):
                pass
        except PermissionError:
            progress.close()
            show_error(
                f"File is currently open in Excel or locked by another process.\n\n"
                f"Please close the file and try again.\n\n"
                f"File: {user_excel_path}",
                parent=parent
            )
            log_event(
                "sap.creation",
                "Excel file is locked",
                level="warning",
                details={"file": user_excel_path},
            )
            return
        
        progress.setLabelText("Reading Excel data...")
        QtWidgets.QApplication.processEvents()
        
        user_df = pd.read_excel(user_excel_path, engine="openpyxl")
        
        progress.close()
    except PermissionError as exc:
        progress.close()
        log_event(
            "sap.creation",
            "Permission denied reading SAP Excel",
            level="error",
            details={"error": str(exc), "file": user_excel_path},
        )
        show_error(
            f"Permission denied. The file may be open in Excel.\n\n"
            f"Please close the file and try again.\n\n"
            f"File: {user_excel_path}",
            parent=parent
        )
        return
    except Exception as exc:  # noqa: BLE001
        progress.close()
        log_event(
            "sap.creation",
            "Unable to read user submitted SAP Excel",
            level="error",
            details={"error": str(exc), "file": user_excel_path},
        )
        show_error(
            f"Failed to read the user submitted Excel.\n\n"
            f"The file may be corrupted or in an unsupported format.\n\n"
            f"Error details: {exc}",
            parent=parent
        )
        return

    cons_path = get_path("consolidated_excel")
    if not cons_path or not os.path.exists(cons_path):
        cons_path = get_open_file(
            "Select Consolidated SAP Excel",
            "Excel files (*.xlsx *.xls);;All files (*.*)",
            parent=parent,
        )
        if not cons_path:
            log_event(
                "sap.creation",
                "SAP creation flow cancelled - consolidated Excel missing",
                level="warning",
            )
            return
        set_path("consolidated_excel", cons_path)

    log_event(
        "sap.creation",
        "Parsing SAP onboarding workbook",
        details={"user_excel": os.path.basename(user_excel_path)},
    )

    # Create progress dialog for parsing
    progress = QtWidgets.QProgressDialog("Processing SAP data...", None, 0, 0, parent)
    progress.setWindowTitle("Processing")
    progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    QtWidgets.QApplication.processEvents()

    try:
        progress.setLabelText("Reading consolidated Excel...")
        QtWidgets.QApplication.processEvents()
        
        # Check if consolidated file is accessible
        if not os.path.exists(cons_path):
            progress.close()
            show_error(f"Consolidated Excel file not found:\n{cons_path}", parent=parent)
            return
        
        existing_emp = get_all_existing_employees(cons_path)
        
        progress.setLabelText("Parsing user data...")
        QtWidgets.QApplication.processEvents()
        
        parsed = parse_user_excel(user_df, existing_emp)
        
        progress.close()
    except PermissionError as exc:
        progress.close()
        log_event(
            "sap.creation",
            "Consolidated Excel file is locked",
            level="error",
            details={"error": str(exc), "file": cons_path},
        )
        show_error(
            f"Cannot access consolidated Excel file.\n\n"
            f"The file may be open in Excel. Please close it and try again.\n\n"
            f"File: {cons_path}",
            parent=parent
        )
        return
    except Exception as exc:  # noqa: BLE001
        progress.close()
        log_event(
            "sap.creation",
            "Failed to parse SAP onboarding workbook",
            level="error",
            details={"error": str(exc)},
        )
        show_error(
            f"Unable to parse SAP onboarding Excel.\n\n"
            f"Error details: {exc}",
            parent=parent
        )
        return

    if not parsed.rows_to_append and not parsed.already_created:
        log_event(
            "sap.creation",
            "SAP onboarding workbook contained no actionable rows",
            level="warning",
        )
        show_info("No valid employees found.", title="Nothing to process", parent=parent)
        return

    log_event(
        "sap.creation",
        "Launching SAP onboarding preview",
        details={"pending_rows": len(parsed.rows_to_append)},
    )
    
    # Ensure all Qt events are processed before showing Tkinter window
    QtWidgets.QApplication.processEvents()
    
    build_preview_window(
        parsed.rows_to_append,
        parsed.already_created,
        cons_path,
        user_excel_path,
        parsed.other_desc_map,
    )


class SapSupportDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SAP S4 Account Support")
        self.setMinimumSize(680, 520)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        subtitle = QtWidgets.QLabel("Attach support details and ticket screenshot for escalation")
        subtitle.setProperty("role", "caption")
        layout.addWidget(subtitle)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.emp_id = QtWidgets.QLineEdit()
        self.ticket_no = QtWidgets.QLineEdit()
        form.addRow("Employee ID", self.emp_id)
        form.addRow("Ticket Number", self.ticket_no)
        layout.addLayout(form)

        self.support_type = QtWidgets.QComboBox()
        self.support_type.addItems([
            "password_reset",
            "unlock_account",
            "role_adjustment",
            "other_support",
        ])
        layout.addWidget(self.support_type)

        self.screenshot_path = QtWidgets.QLineEdit()
        self.screenshot_path.setPlaceholderText("Ticket screenshot path")
        browse = QtWidgets.QPushButton("Select Screenshot")
        browse.clicked.connect(self._select_screenshot)
        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(self.screenshot_path, 1)
        path_row.addWidget(browse)
        layout.addLayout(path_row)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Submit Request")
        submit_btn.setStyleSheet(f"background-color: {ACCENT}; color: #051221; font-weight: 700;")
        submit_btn.clicked.connect(self._submit)
        footer.addWidget(cancel_btn)
        footer.addWidget(submit_btn)
        layout.addLayout(footer)

    def _select_screenshot(self) -> None:
        default_dir = get_path("sap_ticket_image_dir")
        path = get_open_file(
            "Select Ticket Screenshot",
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*.*)",
            parent=self,
            directory=default_dir,
        )
        if path:
            self.screenshot_path.setText(path)
            set_path("sap_ticket_image_dir", os.path.dirname(path))

    def _submit(self) -> None:
        emp_id = self.emp_id.text().strip()
        ticket_no = self.ticket_no.text().strip()
        screenshot = self.screenshot_path.text().strip()
        if not emp_id:
            show_error("Employee ID is required.", parent=self)
            self.emp_id.setFocus()
            return
        if not ticket_no:
            show_error("Ticket number is required.", parent=self)
            self.ticket_no.setFocus()
            return
        if not screenshot:
            show_error("Ticket screenshot is required.", parent=self)
            return
        if not os.path.exists(screenshot):
            show_error("Selected screenshot file could not be found.", parent=self)
            return

        if not ask_yes_no(
            f"Submit support request for {emp_id}?\nTicket: {ticket_no}",
            title="Confirm Submission",
            parent=self,
        ):
            return

        try:
            send_sap_support_email(emp_id, ticket_no, screenshot, self.support_type.currentText())
        except Exception as exc:  # noqa: BLE001
            log_event(
                "sap.support",
                "SAP support email failed",
                level="error",
                details={"error": str(exc), "employee": emp_id, "ticket": ticket_no},
            )
            show_error(f"Failed to send SAP support email.\n\nDetails: {exc}", parent=self)
            return

        log_event(
            "sap.support",
            "SAP support email dispatched",
            details={"employee": emp_id, "ticket": ticket_no},
        )
        show_info(f"Support email sent for {emp_id}.", title="Success", parent=self)
        self.accept()


def launch_sap_support(parent: QtWidgets.QWidget | None = None) -> None:
    dialog = SapSupportDialog(parent)
    dialog.exec()


class SapDisableDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SAP S4 Disable Accounts")
        self.setModal(True)
        self.setMinimumSize(640, 520)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(16)

        info = QtWidgets.QLabel("Queue employee IDs to mark as disabled in the consolidated SAP workbook.")
        info.setWordWrap(True)
        info.setProperty("role", "caption")
        layout.addWidget(info)

        entry_row = QtWidgets.QHBoxLayout()
        self.employee_field = QtWidgets.QLineEdit()
        self.employee_field.setPlaceholderText("Employee ID")
        add_btn = QtWidgets.QPushButton("Add")
        add_btn.setStyleSheet(f"background-color: {SUCCESS}; color: #051221;")
        add_btn.clicked.connect(self.add_employee)
        entry_row.addWidget(self.employee_field, 1)
        entry_row.addWidget(add_btn)
        layout.addLayout(entry_row)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget, 1)

        remove_btn = QtWidgets.QPushButton("Remove Selected")
        remove_btn.setStyleSheet(f"background-color: {DANGER}; color: #051221;")
        remove_btn.clicked.connect(self.remove_employee)
        layout.addWidget(remove_btn)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Disable Accounts")
        submit_btn.setStyleSheet(f"background-color: {ACCENT}; color: #051221; font-weight: 700;")
        submit_btn.clicked.connect(self.submit)
        footer.addWidget(cancel_btn)
        footer.addWidget(submit_btn)
        layout.addLayout(footer)

        self.employees: List[str] = []

    def add_employee(self) -> None:
        value = self.employee_field.text().strip()
        if not value:
            show_error("Employee ID is required before adding.", parent=self)
            return
        self.employees.append(value)
        self._refresh()
        self.employee_field.clear()
        self.employee_field.setFocus()

    def remove_employee(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            show_warning("Select an employee to remove.", parent=self)
            return
        self.employees.pop(row)
        self._refresh()

    def submit(self) -> None:
        if not self.employees:
            show_error("Add at least one employee ID.", parent=self)
            return

        log_event("sap.disable", "Preparing SAP disable workflow", details={"count": len(self.employees)})

        cons_path = get_path("consolidated_excel")
        if not cons_path or not os.path.exists(cons_path):
            cons_path = get_open_file(
                "Select Consolidated SAP Excel",
                "Excel files (*.xlsx *.xls);;All files (*.*)",
                parent=self,
            )
            if not cons_path:
                return
            set_path("consolidated_excel", cons_path)

        if not ask_yes_no(
            f"Disable SAP accounts for {len(self.employees)} employee(s)?\nThis will mark STATUS as 'Disabled'.",
            title="Confirm Disable",
            parent=self,
        ):
            log_event(
                "sap.disable",
                "SAP disable workflow cancelled at confirmation",
                level="warning",
                details={"count": len(self.employees)},
            )
            return

        try:
            result = disable_sap_accounts(cons_path, self.employees)
        except PermissionError:
            log_event(
                "sap.disable",
                "Consolidated Excel locked during disable workflow",
                level="error",
                details={"file": cons_path},
            )
            show_error(
                "Cannot save to consolidated Excel file.\nPlease close the file in Excel and try again.",
                title="File Locked",
                parent=self,
            )
            return
        except Exception as exc:  # noqa: BLE001
            log_event(
                "sap.disable",
                "SAP disable workflow failed",
                level="error",
                details={"error": str(exc)},
            )
            show_error(f"Error disabling accounts:\n\n{exc}", parent=self)
            return

        summary_lines = []
        if result.updated:
            summary_lines.append(f"✅ UPDATED ({len(result.updated)}):")
            summary_lines.extend([f"  • {emp}" for emp in result.updated])
        if result.not_found:
            summary_lines.append("")
            summary_lines.append(f"❌ NOT FOUND ({len(result.not_found)}):")
            summary_lines.extend([f"  • {emp}" for emp in result.not_found])
        summary_lines.append("")
        summary_lines.append(f"Total Updated: {len(result.updated)}")
        summary_lines.append(f"Not in List: {len(result.not_found)}")

        show_info("\n".join(summary_lines), title="Disable Summary", parent=self)
        log_event(
            "sap.disable",
            "SAP accounts updated in consolidated workbook",
            details={"updated": len(result.updated), "not_found": len(result.not_found)},
        )

        if result.updated:
            ticket_no, ok = QtWidgets.QInputDialog.getText(
                self,
                "Ticket Number",
                "Enter ticket number (e.g. SAA122212):",
            )
            if not ok or not ticket_no.strip():
                show_warning("Ticket number is required. Email not sent.", parent=self)
                self.accept()
                return

            ticket_img_path = get_open_file(
                "Select Ticket Image File",
                "Image files (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*.*)",
                parent=self,
                directory=get_path("sap_ticket_image_dir"),
            )
            if not ticket_img_path:
                show_warning("Ticket image is required. Email not sent.", parent=self)
                self.accept()
                return

            set_path("sap_ticket_image_dir", os.path.dirname(ticket_img_path))

            try:
                send_sap_disable_email(result.updated, ticket_no.strip(), ticket_img_path)
            except Exception as exc:  # noqa: BLE001
                log_event(
                    "sap.disable",
                    "Failed to dispatch SAP disable email",
                    level="error",
                    details={"error": str(exc), "ticket": ticket_no.strip()},
                )
                show_error(
                    f"Failed to send disable confirmation email.\n\nDetails: {exc}",
                    parent=self,
                )
                self.accept()
                return

            log_event(
                "sap.disable",
                "SAP disable email dispatched",
                details={"ticket": ticket_no.strip(), "count": len(result.updated)},
            )
            show_info("Disable email sent successfully.", title="Success", parent=self)

        self.accept()

    def _refresh(self) -> None:
        self.list_widget.clear()
        for idx, emp in enumerate(self.employees, start=1):
            self.list_widget.addItem(f"{idx:02d} • {emp}")


def launch_sap_disable(parent: QtWidgets.QWidget | None = None) -> None:
    dialog = SapDisableDialog(parent)
    dialog.exec()


# ---------------------------------------------------------------------------
# Agile workflows
# ---------------------------------------------------------------------------


class AgileCreationDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Agile Account Creation")
        self.setModal(True)
        self.setMinimumSize(720, 680)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(16)

        # System selection with clear styling
        systems_group = QtWidgets.QGroupBox("Select Agile Systems")
        systems_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {ACCENT};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: {CARD_BG};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
                font-size: 13px;
                color: {ACCENT};
                font-weight: 700;
            }}
            QCheckBox {{
                spacing: 12px;
                font-size: 14px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border: 2px solid {ACCENT};
                border-radius: 6px;
                background-color: {SURFACE_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
            QCheckBox::indicator:hover {{
                border-color: {INFO};
                background-color: {ELEVATED_BG};
            }}
        """)
        
        systems_layout = QtWidgets.QHBoxLayout(systems_group)
        systems_layout.setSpacing(24)
        systems_layout.setContentsMargins(20, 20, 20, 20)
        
        self.system_checks: Dict[str, QtWidgets.QCheckBox] = {}
        for system in ["MFG Agile", "RD Agile"]:
            checkbox = QtWidgets.QCheckBox(system)
            checkbox.setChecked(True)  # Both checked by default
            checkbox.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.system_checks[system.split()[0]] = checkbox
            systems_layout.addWidget(checkbox)
        systems_layout.addStretch(1)
        
        layout.addWidget(systems_group)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.ticket_no = QtWidgets.QLineEdit()
        self.ticket_no.setPlaceholderText("Ticket number")
        form.addRow("Ticket Number", self.ticket_no)
        layout.addLayout(form)

        list_section = QtWidgets.QGroupBox("Employee Queue")
        list_layout = QtWidgets.QVBoxLayout(list_section)
        entry_row = QtWidgets.QHBoxLayout()
        self.employee_field = QtWidgets.QLineEdit()
        self.employee_field.setPlaceholderText("Employee ID")
        add_btn = QtWidgets.QPushButton("Add")
        add_btn.setStyleSheet(f"background-color: {SUCCESS}; color: #051221;")
        add_btn.clicked.connect(self.add_employee)
        entry_row.addWidget(self.employee_field, 1)
        entry_row.addWidget(add_btn)
        list_layout.addLayout(entry_row)
        self.list_widget = QtWidgets.QListWidget()
        list_layout.addWidget(self.list_widget, 1)
        remove_btn = QtWidgets.QPushButton("Remove Selected")
        remove_btn.setStyleSheet(f"background-color: {DANGER}; color: #051221;")
        remove_btn.clicked.connect(self.remove_employee)
        list_layout.addWidget(remove_btn)
        layout.addWidget(list_section)

        screenshot_row = QtWidgets.QHBoxLayout()
        self.screenshot_path = QtWidgets.QLineEdit()
        self.screenshot_path.setPlaceholderText("Ticket screenshot path")
        browse = QtWidgets.QPushButton("Select Screenshot")
        browse.clicked.connect(self._select_screenshot)
        screenshot_row.addWidget(self.screenshot_path, 1)
        screenshot_row.addWidget(browse)
        layout.addLayout(screenshot_row)

        self.ticket_text = QtWidgets.QTextEdit()
        self.ticket_text.setPlaceholderText("Paste ticket content here…")
        layout.addWidget(self.ticket_text, 1)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Send Request")
        submit_btn.setStyleSheet(f"background-color: {ACCENT}; color: #051221; font-weight: 700;")
        submit_btn.clicked.connect(self.submit)
        footer.addWidget(cancel_btn)
        footer.addWidget(submit_btn)
        layout.addLayout(footer)

        self.employees: List[str] = []

    def add_employee(self) -> None:
        value = self.employee_field.text().strip()
        if not value:
            show_error("Employee ID is required before adding.", parent=self)
            return
        self.employees.append(value)
        self._refresh()
        self.employee_field.clear()
        self.employee_field.setFocus()

    def remove_employee(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            show_warning("Select an employee to remove.", parent=self)
            return
        self.employees.pop(row)
        self._refresh()

    def _select_screenshot(self) -> None:
        default_dir = get_path("agile_ticket_image_dir")
        path = get_open_file(
            "Select Ticket Screenshot",
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*.*)",
            parent=self,
            directory=default_dir,
        )
        if path:
            self.screenshot_path.setText(path)
            set_path("agile_ticket_image_dir", os.path.dirname(path))

    def submit(self) -> None:
        selected_systems = [label for label, checkbox in self.system_checks.items() if checkbox.isChecked()]
        if not selected_systems:
            show_error("Select at least one Agile system.", parent=self)
            return
        if not self.ticket_no.text().strip():
            show_error("Ticket number is required.", parent=self)
            self.ticket_no.setFocus()
            return
        if not self.employees:
            show_error("Add at least one employee ID.", parent=self)
            return
        screenshot_path = self.screenshot_path.text().strip()
        if not screenshot_path:
            show_error("Ticket screenshot is required.", parent=self)
            return
        if not os.path.exists(screenshot_path):
            show_error("Selected screenshot file could not be found.", parent=self)
            return
        ticket_text = self.ticket_text.toPlainText().strip()
        if not ticket_text:
            show_error("Paste the ticket content into the form.", parent=self)
            return

        log_event(
            "agile.creation",
            "Preparing Agile account creation email",
            details={"systems": selected_systems, "count": len(self.employees)},
        )

        try:
            send_agile_creation_email(
                [{"Employee ID": emp} for emp in self.employees],
                selected_systems,
                self.ticket_no.text().strip(),
                self.employees,
                screenshot_path,
                ticket_text,
            )
        except Exception as exc:  # noqa: BLE001
            log_event(
                "agile.creation",
                "Agile account creation email failed",
                level="error",
                details={"error": str(exc), "ticket": self.ticket_no.text().strip()},
            )
            show_error(
                f"Failed to prepare Agile account creation email.\n\nDetails: {exc}",
                parent=self,
            )
            return

        log_event(
            "agile.creation",
            "Agile account creation email prepared",
            details={"ticket": self.ticket_no.text().strip(), "count": len(self.employees)},
        )
        show_info("Agile account creation email prepared and sent.", title="Success", parent=self)
        self.accept()

    def _refresh(self) -> None:
        self.list_widget.clear()
        for idx, emp in enumerate(self.employees, start=1):
            self.list_widget.addItem(f"{idx:02d} • {emp}")


def launch_agile_creation(parent: QtWidgets.QWidget | None = None) -> None:
    dialog = AgileCreationDialog(parent)
    dialog.exec()


class AgileResetDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Agile Password Reset")
        self.setModal(True)
        self.setMinimumSize(520, 480)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(16)

        # System selection with clear styling
        systems_group = QtWidgets.QGroupBox("Select Agile Systems")
        systems_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {ACCENT};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: {CARD_BG};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
                font-size: 13px;
                color: {ACCENT};
                font-weight: 700;
            }}
            QCheckBox {{
                spacing: 12px;
                font-size: 14px;
                font-weight: 600;
                color: {TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border: 2px solid {ACCENT};
                border-radius: 6px;
                background-color: {SURFACE_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ACCENT};
                border-color: {ACCENT};
            }}
            QCheckBox::indicator:hover {{
                border-color: {INFO};
                background-color: {ELEVATED_BG};
            }}
        """)
        
        systems_layout = QtWidgets.QHBoxLayout(systems_group)
        systems_layout.setSpacing(24)
        systems_layout.setContentsMargins(20, 20, 20, 20)
        
        self.system_checks: Dict[str, QtWidgets.QCheckBox] = {}
        for system in ["MFG Agile", "RD Agile"]:
            checkbox = QtWidgets.QCheckBox(system)
            checkbox.setChecked(True)  # Both checked by default
            checkbox.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.system_checks[system.split()[0]] = checkbox
            systems_layout.addWidget(checkbox)
        systems_layout.addStretch(1)
        
        layout.addWidget(systems_group)

        form = QtWidgets.QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        self.ticket_no = QtWidgets.QLineEdit()
        self.ticket_no.setPlaceholderText("Ticket number")
        self.employee_id = QtWidgets.QLineEdit()
        self.employee_id.setPlaceholderText("Employee ID")
        form.addRow("Ticket Number", self.ticket_no)
        form.addRow("Employee ID", self.employee_id)
        layout.addLayout(form)

        screenshot_row = QtWidgets.QHBoxLayout()
        self.screenshot_path = QtWidgets.QLineEdit()
        self.screenshot_path.setPlaceholderText("Ticket screenshot path")
        browse = QtWidgets.QPushButton("Select Screenshot")
        browse.clicked.connect(self._select_screenshot)
        screenshot_row.addWidget(self.screenshot_path, 1)
        screenshot_row.addWidget(browse)
        layout.addLayout(screenshot_row)

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Send Reset")
        submit_btn.setStyleSheet(f"background-color: {ACCENT}; color: #051221; font-weight: 700;")
        submit_btn.clicked.connect(self.submit)
        footer.addWidget(cancel_btn)
        footer.addWidget(submit_btn)
        layout.addLayout(footer)

    def _select_screenshot(self) -> None:
        default_dir = get_path("agile_ticket_image_dir")
        path = get_open_file(
            "Select Ticket Screenshot",
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*.*)",
            parent=self,
            directory=default_dir,
        )
        if path:
            self.screenshot_path.setText(path)
            set_path("agile_ticket_image_dir", os.path.dirname(path))

    def submit(self) -> None:
        selected_systems = [label for label, checkbox in self.system_checks.items() if checkbox.isChecked()]
        if not selected_systems:
            show_error("Select at least one Agile system.", parent=self)
            return
        ticket_no = self.ticket_no.text().strip()
        if not ticket_no:
            show_error("Ticket number is required.", parent=self)
            self.ticket_no.setFocus()
            return
        emp_id = self.employee_id.text().strip()
        if not emp_id:
            show_error("Employee ID is required.", parent=self)
            self.employee_id.setFocus()
            return
        screenshot_path = self.screenshot_path.text().strip()
        if not screenshot_path:
            show_error("Ticket screenshot is required.", parent=self)
            return
        if not os.path.exists(screenshot_path):
            show_error("Selected screenshot file could not be found.", parent=self)
            return

        log_event(
            "agile.reset",
            "Preparing Agile password reset email",
            details={"systems": selected_systems, "employee": emp_id},
        )

        try:
            send_agile_reset_email(selected_systems, ticket_no, emp_id, screenshot_path)
        except Exception as exc:  # noqa: BLE001
            log_event(
                "agile.reset",
                "Agile password reset email failed",
                level="error",
                details={"error": str(exc), "ticket": ticket_no},
            )
            show_error(
                f"Failed to prepare Agile password reset email.\n\nDetails: {exc}",
                parent=self,
            )
            return

        log_event(
            "agile.reset",
            "Agile password reset email prepared",
            details={"ticket": ticket_no, "employee": emp_id},
        )
        show_info("Agile password reset email prepared and sent.", title="Success", parent=self)
        self.accept()


def launch_agile_reset(parent: QtWidgets.QWidget | None = None) -> None:
    dialog = AgileResetDialog(parent)
    dialog.exec()


# ---------------------------------------------------------------------------
# Telco workflows
# ---------------------------------------------------------------------------


def launch_singtel_process(parent: QtWidgets.QWidget | None = None) -> None:
    pdf1 = get_open_file(
        "Select First PDF (will be renamed to IGS SIP)",
        "PDF files (*.pdf);;All files (*.*)",
        parent=parent,
    )
    if not pdf1:
        log_event("telco.singtel", "Singtel process cancelled - missing first PDF", level="warning")
        return

    pdf2 = get_open_file(
        "Select Second PDF (will be renamed to IGS Telco)",
        "PDF files (*.pdf);;All files (*.*)",
        parent=parent,
    )
    if not pdf2:
        log_event("telco.singtel", "Singtel process cancelled - missing second PDF", level="warning")
        return

    igs32_path = get_path("singtel_igs32_path")
    if not igs32_path:
        igs32_path = get_existing_directory("Select Singtel-IGS.32 folder path", parent=parent)
        if not igs32_path:
            show_error("IGS.32 path is required.", parent=parent)
            return
        set_path("singtel_igs32_path", igs32_path)

    cnt35_path = get_path("singtel_cnt35_path")
    if not cnt35_path:
        cnt35_path = get_existing_directory("Select Singtel-CNT.35 folder path", parent=parent)
        if not cnt35_path:
            show_error("CNT.35 path is required.", parent=parent)
            return
        set_path("singtel_cnt35_path", cnt35_path)

    if not ask_yes_no(
        (
            "Process Singtel bills?\n\n"
            f"PDF 1: {os.path.basename(pdf1)}\n"
            f"PDF 2: {os.path.basename(pdf2)}\n\n"
            f"Files will be copied to:\n- {igs32_path}\n- {cnt35_path}\n\n"
            "Email will be sent after processing."
        ),
        title="Confirm Singtel Process",
        parent=parent,
    ):
        log_event(
            "telco.singtel",
            "Singtel process cancelled at confirmation",
            level="warning",
            details={"pdf1": os.path.basename(pdf1), "pdf2": os.path.basename(pdf2)},
        )
        return

    try:
        log_event(
            "telco.singtel",
            "Processing Singtel bills",
            details={
                "pdf1": os.path.basename(pdf1),
                "pdf2": os.path.basename(pdf2),
                "igs32": igs32_path,
                "cnt35": cnt35_path,
            },
        )
        result = process_singtel_bills(pdf1, pdf2, igs32_path, cnt35_path)
        send_singtel_telco_email(
            result["sip_igs32"],
            result["telco_igs32"],
            result["igs32_path"],
        )
        log_event(
            "telco.singtel",
            "Singtel bills processed and email dispatched",
            details={"igs32_output": result["igs32_path"], "cnt35_output": cnt35_path},
        )
        show_info(
            (
                "Singtel bills processed successfully!\n\n"
                f"Files saved to:\n- IGS.32: {igs32_path}\n- CNT.35: {cnt35_path}\n\n"
                "Email sent with attachments."
            ),
            title="Success",
            parent=parent,
        )
    except Exception as exc:  # noqa: BLE001
        log_event(
            "telco.singtel",
            "Singtel bill processing failed",
            level="error",
            details={"error": str(exc)},
        )
        show_error(f"Error processing Singtel bills:\n\n{exc}", parent=parent)


def launch_m1_process(parent: QtWidgets.QWidget | None = None) -> None:
    pdf_path = get_open_file(
        "Select M1 bill PDF",
        "PDF files (*.pdf);;All files (*.*)",
        parent=parent,
    )
    if not pdf_path:
        log_event("telco.m1", "M1 process cancelled - PDF not selected", level="warning")
        return

    igs32_path = get_path("m1_igs32_path")
    if not igs32_path:
        igs32_path = get_existing_directory("Select M1-IGS.32 folder path", parent=parent)
        if not igs32_path:
            show_error("IGS.32 path is required.", parent=parent)
            return
        set_path("m1_igs32_path", igs32_path)

    cnt35_path = get_path("m1_cnt35_path")
    if not cnt35_path:
        cnt35_path = get_existing_directory("Select M1-CNT.35 folder path", parent=parent)
        if not cnt35_path:
            show_error("CNT.35 path is required.", parent=parent)
            return
        set_path("m1_cnt35_path", cnt35_path)

    igs32_excel = get_path("m1_igs32_excel")
    if not igs32_excel:
        igs32_excel = get_open_file("Select IGS.32 Excel", "Excel files (*.xlsx *.xls)", parent=parent)
        if not igs32_excel:
            show_error("IGS.32 Excel path is required.", parent=parent)
            return
        set_path("m1_igs32_excel", igs32_excel)

    cnt35_excel = get_path("m1_cnt35_excel")
    if not cnt35_excel:
        cnt35_excel = get_open_file("Select CNT.35 Excel", "Excel files (*.xlsx *.xls)", parent=parent)
        if not cnt35_excel:
            show_error("CNT.35 Excel path is required.", parent=parent)
            return
        set_path("m1_cnt35_excel", cnt35_excel)

    amount, ok = QtWidgets.QInputDialog.getDouble(
        _active_parent(parent),
        "M1 Bill Amount",
        "Enter total amount with GST:",
        value=0.0,
        minValue=0.0,
        maxValue=999999.99,
        decimals=2,
    )
    if not ok:
        show_warning("Amount is required.", parent=parent)
        log_event("telco.m1", "M1 process cancelled - amount not provided", level="warning")
        return

    if not ask_yes_no(
        (
            "Process M1 bill?\n\n"
            f"PDF: {os.path.basename(pdf_path)}\n"
            f"Amount (with GST): ${amount:.2f}\n\n"
            f"Files will be copied to:\n- {igs32_path}\n- {cnt35_path}\n\n"
            "Excel files will be updated and email will be sent."
        ),
        title="Confirm M1 Process",
        parent=parent,
    ):
        log_event(
            "telco.m1",
            "M1 process cancelled at confirmation",
            level="warning",
            details={"pdf": os.path.basename(pdf_path), "amount": amount},
        )
        return

    try:
        log_event(
            "telco.m1",
            "Processing M1 bill",
            details={
                "pdf": os.path.basename(pdf_path),
                "amount": amount,
                "igs32_path": igs32_path,
                "cnt35_path": cnt35_path,
            },
        )
        result = process_m1_bill(pdf_path, igs32_path, cnt35_path)
        excel_results = update_both_m1_excels(igs32_excel, cnt35_excel, amount)

        summary_lines = ["M1 bill processed successfully!", ""]
        summary_lines.append("PDF saved to both paths.")
        summary_lines.append("")

        if excel_results["igs32"]["success"]:
            prev_month = excel_results["igs32"].get("prev_month")
            prev_amount = excel_results["igs32"].get("prev_amount", 0.0)
            summary_lines.append("IGS.32 Excel updated:")
            summary_lines.append(f"  Previous: {prev_month} = ${prev_amount:.2f}")
            summary_lines.append(f"  Current: ${amount:.2f}")
        else:
            summary_lines.append(
                f"IGS.32 Excel update failed: {excel_results['igs32'].get('error', 'Unknown error')}"
            )

        summary_lines.append("")
        if excel_results["cnt35"]["success"]:
            summary_lines.append("CNT.35 Excel updated successfully.")
        else:
            summary_lines.append(
                f"CNT.35 Excel update failed: {excel_results['cnt35'].get('error', 'Unknown error')}"
            )

        show_info("\n".join(summary_lines), title="Process Summary", parent=parent)
        send_m1_telco_email(result["m1_igs32"])
        log_event(
            "telco.m1",
            "M1 bill processed and email dispatched",
            details={
                "amount": amount,
                "igs32_pdf": result["m1_igs32"],
                "igs32_excel": igs32_excel,
                "cnt35_excel": cnt35_excel,
            },
        )
        show_info("Email sent successfully!", title="Success", parent=parent)
    except PermissionError:
        log_event(
            "telco.m1",
            "Excel file locked during M1 process",
            level="error",
            details={"igs32_excel": igs32_excel, "cnt35_excel": cnt35_excel},
        )
        show_error(
            "Cannot update Excel file.\nPlease close the Excel file and try again.",
            title="File Locked",
            parent=parent,
        )
    except Exception as exc:  # noqa: BLE001
        log_event(
            "telco.m1",
            "M1 bill processing failed",
            level="error",
            details={"error": str(exc)},
        )
        show_error(f"Error processing M1 bill:\n\n{exc}", parent=parent)


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Environment Settings")
        self.setMinimumSize(1100, 700)
        self.setModal(True)

        self.profile_var = QtWidgets.QComboBox()
        self.profile_var.currentTextChanged.connect(self.on_profile_selected)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        profile_row = QtWidgets.QHBoxLayout()
        profile_row.addWidget(QtWidgets.QLabel("Active Profile"))
        profile_row.addWidget(self.profile_var, 1)
        create_btn = QtWidgets.QPushButton("Create Profile")
        create_btn.clicked.connect(self.create_profile)
        delete_btn = QtWidgets.QPushButton("Delete Profile")
        delete_btn.setStyleSheet(f"background-color: {DANGER}; color: #051221;")
        delete_btn.clicked.connect(self.delete_profile)
        profile_row.addWidget(create_btn)
        profile_row.addWidget(delete_btn)
        layout.addLayout(profile_row)

        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.paths_tab = QtWidgets.QWidget()
        self.email_tab = QtWidgets.QWidget()
        self.signature_tab = QtWidgets.QWidget()
        self.backups_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.paths_tab, "Paths")
        self.tabs.addTab(self.email_tab, "Email Recipients")
        self.tabs.addTab(self.signature_tab, "Signature")
        self.tabs.addTab(self.backups_tab, "Backups")

        self.path_entries: Dict[str, QtWidgets.QLineEdit] = {}
        self.email_entries: Dict[tuple[str, str], QtWidgets.QLineEdit] = {}
        self.signature_editor = QtWidgets.QPlainTextEdit()
        self.backups_list = QtWidgets.QListWidget()

        self._build_paths_tab()
        self._build_email_tab()
        self._build_signature_tab()
        self._build_backups_tab()

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        footer.addWidget(close_btn)
        footer.addWidget(save_btn)
        layout.addLayout(footer)

        self.refresh_profiles()

    def _build_paths_tab(self) -> None:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        
        container = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(container)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(12)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        for key in sorted(list_paths(get_active_profile_name()).keys()):
            entry = QtWidgets.QLineEdit()
            entry.setMinimumWidth(500)
            browse = QtWidgets.QPushButton("📁 Browse")
            browse.setFixedWidth(120)
            browse.clicked.connect(lambda checked=False, k=key: self._browse_path(k))  # noqa: ARG005
            row = QtWidgets.QHBoxLayout()
            row.addWidget(entry, 1)
            row.addWidget(browse)
            container_widget = QtWidgets.QWidget()
            container_widget.setLayout(row)
            
            label = QtWidgets.QLabel(key)
            label.setMinimumWidth(180)
            label.setStyleSheet("font-weight: 600;")
            layout.addRow(label, container_widget)
            self.path_entries[key] = entry
        
        scroll.setWidget(container)
        tab_layout = QtWidgets.QVBoxLayout(self.paths_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def _build_email_tab(self) -> None:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        
        container = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(container)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(12)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        sections = list_email_sections(get_active_profile_name())
        # Filter out non-dict values (like "signature")
        section_keys = sorted([k for k, v in sections.items() if isinstance(v, dict)])
        if not section_keys:
            section_keys = ["notifications"]
        for section in section_keys:
            section_data = sections.get(section, {})
            if not isinstance(section_data, dict):
                continue
            fields = sorted(section_data.keys() or {"to", "cc"})
            for field in fields:
                entry = QtWidgets.QLineEdit()
                entry.setMinimumWidth(500)
                label = QtWidgets.QLabel(f"{section}.{field}")
                label.setMinimumWidth(180)
                label.setStyleSheet("font-weight: 600;")
                layout.addRow(label, entry)
                self.email_entries[(section, field)] = entry
        
        scroll.setWidget(container)
        tab_layout = QtWidgets.QVBoxLayout(self.email_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def _build_signature_tab(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.signature_tab)
        layout.addWidget(QtWidgets.QLabel("HTML footer used for all emails"))
        self.signature_editor.setPlaceholderText("Paste or edit the shared signature block…")
        layout.addWidget(self.signature_editor, 1)

    def _build_backups_tab(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.backups_tab)
        layout.addWidget(QtWidgets.QLabel("Recent configuration backups"))
        layout.addWidget(self.backups_list, 1)

    def refresh_profiles(self) -> None:
        names = list_profiles()
        self.profile_var.blockSignals(True)
        self.profile_var.clear()
        self.profile_var.addItems(names)
        self.profile_var.setCurrentText(get_active_profile_name())
        self.profile_var.blockSignals(False)
        self.populate_fields(self.profile_var.currentText())

    def on_profile_selected(self, profile: str) -> None:
        if not profile:
            return
        current = get_active_profile_name()
        if profile != current:
            try:
                set_active_profile(profile)
            except ValueError as exc:  # noqa: BLE001
                show_error(str(exc), parent=self)
                self.profile_var.setCurrentText(current)
                return
            log_event("config.profile", "Switched active configuration profile", details={"profile": profile})
        self.populate_fields(profile)
        self.refresh_backups()

    def populate_fields(self, profile_name: str) -> None:
        paths = list_paths(profile_name)
        for key, entry in self.path_entries.items():
            entry.setText(paths.get(key, ""))

        sections = list_email_sections(profile_name)
        for (section, field), entry in self.email_entries.items():
            value = ""
            section_data = sections.get(section)
            if isinstance(section_data, dict):
                value = section_data.get(field, "")
            entry.setText(value)

        self.signature_editor.setPlainText(get_signature_text(profile_name))
        self.refresh_backups()

    def refresh_backups(self) -> None:
        self.backups_list.clear()
        for entry in list_config_backups(limit=12):
            timestamp = entry.get("timestamp", "unknown")
            profile = entry.get("active_profile", "default")
            action = entry.get("action", "update")
            backup_file = entry.get("backup_file", "")
            self.backups_list.addItem(f"{timestamp} | {profile} | {action} -> {backup_file}")

    def _browse_path(self, key: str) -> None:
        current = self.path_entries[key].text().strip()
        initial_dir = Path(current).parent.as_posix() if current else os.getcwd()
        if key.endswith(("_folder", "_dir")):
            selected = get_existing_directory(f"Select folder for {key}", parent=self, directory=initial_dir)
        else:
            selected = get_open_file(f"Select file for {key}", "All files (*.*)", parent=self, directory=initial_dir)
        if selected:
            self.path_entries[key].setText(selected)

    def create_profile(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(self, "Create Profile", "Profile name:")
        if not ok or not name.strip():
            return
        try:
            create_profile(name.strip(), source_profile=self.profile_var.currentText())
        except ValueError as exc:  # noqa: BLE001
            show_error(str(exc), parent=self)
            return
        log_event("config.profile", "Created configuration profile", details={"profile": name.strip()})
        self.refresh_profiles()
        self.profile_var.setCurrentText(name.strip())

    def delete_profile(self) -> None:
        target = self.profile_var.currentText()
        if target == "default":
            show_warning("Default profile cannot be deleted.", parent=self)
            return
        if not ask_yes_no(f"Delete profile '{target}'? This cannot be undone.", title="Delete Profile", parent=self):
            return
        try:
            delete_profile(target)
        except ValueError as exc:  # noqa: BLE001
            show_error(str(exc), parent=self)
            return
        log_event("config.profile", "Deleted configuration profile", details={"profile": target})
        self.refresh_profiles()

    def save_settings(self) -> None:
        profile = self.profile_var.currentText()
        paths_payload = {key: entry.text().strip() for key, entry in self.path_entries.items()}
        email_payload: Dict[str, Dict[str, str]] = {}
        for (section, field), entry in self.email_entries.items():
            email_payload.setdefault(section, {})[field] = entry.text().strip()
        signature_value = self.signature_editor.toPlainText().strip()

        try:
            update_profile_settings(
                profile,
                paths=paths_payload,
                email_settings=email_payload,
                signature=signature_value,
            )
        except Exception as exc:  # noqa: BLE001
            show_error(f"Failed to save settings: {exc}", parent=self)
            log_event("config", "Failed to save configuration", level="error", details={"error": str(exc)})
            return

        log_event("config", "Configuration updated", details={"profile": profile})
        show_info(f"Settings saved for profile '{profile}'.", title="Saved", parent=self)
        self.refresh_backups()


def show_settings_dialog(parent: QtWidgets.QWidget | None = None) -> None:
    dialog = SettingsDialog(parent)
    dialog.exec()


# ---------------------------------------------------------------------------
# Tab builders
# ---------------------------------------------------------------------------


def build_user_management_section(parent: QtWidgets.QWidget) -> None:
    # Create scroll area
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # Create container widget for the scroll area
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(18)

    cards = [
        Action(
            title="Create New User Email",
            description="Compose onboarding kits, generate attachments, and dispatch the welcome message.",
            icon="👤",
            accent=SUCCESS,
            handler=lambda widget: MultiUserDialog(
                "New User Email Creation",
                [
                    "User Name",
                    "First Name",
                    "Last Name",
                    "Display Name",
                    "Job Title",
                    "Department",
                    "Employee ID",
                ],
                handle_new_user_email,
                parent=widget.window(),
            ).exec(),
        ),
        Action(
            title="Disable User Email Access",
            description="Queue departing users and send the coordinated disablement instructions.",
            icon="🚫",
            accent=DANGER,
            handler=lambda widget: MultiUserDialog(
                "Disable User Email",
                ["User Name", "Display Name", "Employee ID"],
                handle_disable_user_email,
                parent=widget.window(),
            ).exec(),
        ),
    ]

    for action in cards:
        layout.addWidget(ActionCard(action))
    layout.addStretch(1)
    
    scroll.setWidget(container)
    parent_layout = QtWidgets.QVBoxLayout(parent)
    parent_layout.setContentsMargins(0, 0, 0, 0)
    parent_layout.addWidget(scroll)


def build_sap_section(parent: QtWidgets.QWidget) -> None:
    # Create scroll area
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # Create container widget for the scroll area
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(18)
    
    cards = [
        Action(
            title="Process SAP S4 Account Creation",
            description="Review onboarding workbooks, detect duplicates, and preview upload batches.",
            icon="🔄",
            accent=INFO,
            handler=lambda widget: launch_sap_flow(widget.window()),
        ),
        Action(
            title="SAP S4 Account Support",
            description="Send escalations with ticket evidence for account unlocks or adjustments.",
            icon="🛠",
            accent=ACCENT,
            handler=lambda widget: launch_sap_support(widget.window()),
        ),
        Action(
            title="Disable SAP S4 Account",
            description="Mark employee IDs as disabled within the consolidated workbook for compliance.",
            icon="🛑",
            accent=DANGER,
            handler=lambda widget: launch_sap_disable(widget.window()),
        ),
    ]
    for action in cards:
        layout.addWidget(ActionCard(action))
    layout.addStretch(1)
    
    scroll.setWidget(container)
    parent_layout = QtWidgets.QVBoxLayout(parent)
    parent_layout.setContentsMargins(0, 0, 0, 0)
    parent_layout.addWidget(scroll)


def build_agile_section(parent: QtWidgets.QWidget) -> None:
    # Create scroll area
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # Create container widget for the scroll area
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(18)
    
    cards = [
        Action(
            title="Create Agile Account",
            description="Generate multi-system Agile onboarding emails with ticket context and screenshots.",
            icon="➕",
            accent=SUCCESS,
            handler=lambda widget: launch_agile_creation(widget.window()),
        ),
        Action(
            title="Reset Agile Password",
            description="Coordinate password resets across Agile environments with ticket traceability.",
            icon="🔑",
            accent=ACCENT,
            handler=lambda widget: launch_agile_reset(widget.window()),
        ),
    ]
    for action in cards:
        layout.addWidget(ActionCard(action))
    layout.addStretch(1)
    
    scroll.setWidget(container)
    parent_layout = QtWidgets.QVBoxLayout(parent)
    parent_layout.setContentsMargins(0, 0, 0, 0)
    parent_layout.addWidget(scroll)


def build_telco_section(parent: QtWidgets.QWidget) -> None:
    # Create scroll area
    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # Create container widget for the scroll area
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(18)

    warning_banner = QtWidgets.QLabel(
        "⚠ IMPORTANT: Ensure signatures for both Singtel and M1 are ready before running the automation."
    )
    warning_banner.setWordWrap(True)
    warning_banner.setStyleSheet(
        f"background-color: rgba(251, 191, 36, 0.12); color: {WARNING}; padding: 14px 16px; border-radius: 12px;"
    )
    layout.addWidget(warning_banner)

    cards = [
        Action(
            title="Process Singtel Bills",
            description="Copy PDFs to distribution folders and send the monthly Singtel billing package.",
            icon="📄",
            accent=INFO,
            handler=lambda widget: launch_singtel_process(widget.window()),
        ),
        Action(
            title="Process M1 Bill",
            description="Copy PDFs, update Excel trackers, and send the M1 monthly billing notification.",
            icon="📱",
            accent=SUCCESS,
            handler=lambda widget: launch_m1_process(widget.window()),
        ),
    ]
    for action in cards:
        layout.addWidget(ActionCard(action))
    layout.addStretch(1)
    
    scroll.setWidget(container)
    parent_layout = QtWidgets.QVBoxLayout(parent)
    parent_layout.setContentsMargins(0, 0, 0, 0)
    parent_layout.addWidget(scroll)


__all__ = [
    "ACCENT",
    "apply_dark_tech_palette",
    "build_agile_section",
    "build_sap_section",
    "build_telco_section",
    "build_user_management_section",
    "DANGER",
    "INFO",
    "show_settings_dialog",
    "SUCCESS",
    "TEXT_PRIMARY",
    "TEXT_MUTED",
]
