"""Outlook email helpers for the IT admin tool."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List

import win32com.client

from config_manager import get_email_settings, get_signature_text


def _attach_files(mail, attachments: List[str]) -> None:
    for path in attachments:
        if path and os.path.exists(path):
            mail.Attachments.Add(path)


def _signature_text() -> str:
    return get_signature_text()


def _signature_html() -> str:
    return "<br>".join(get_signature_text().splitlines())


def send_new_user_email(user_list: List[Dict[str, str]], attachments: List[str]) -> None:
    settings = get_email_settings("new_user")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    employee_ids = [user["Employee ID"] for user in user_list]
    mail.Subject = f"Create New User Email Accounts - {', '.join(employee_ids)}"

    email_body = ["Hi Ray/Benni,", ""]
    for idx, user_data in enumerate(user_list, start=1):
        email_body.append(f"    {idx}. 请协助创建 {user_data['User Name']} 并加入 ingrasys-sgp 群组.")

    email_body.extend([
        "",
        "谢谢",
        "",
        "默认开启2FA",
        "",
        "原因：新员工入职",
        "",
        _signature_text()
    ])

    mail.Body = "\n".join(email_body)
    _attach_files(mail, attachments)
    mail.Send()


def send_disable_user_email(user_list: List[Dict[str, str]]) -> None:
    settings = get_email_settings("disable_user")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    employee_ids = [user["Employee ID"] for user in user_list]
    display_names = [user["Display Name"] for user in user_list]
    mail.Subject = f"Disable {', '.join(display_names)} User Email Account - {', '.join(employee_ids)}"

    email_body = ["Hi Ray/Benni,", ""]
    for idx, user_data in enumerate(user_list, start=1):
        email_body.append(f"    {idx}. 请帮忙移除 {user_data['User Name']} 的邮箱并退出全部群组。")

    email_body.extend([
        "",
        "原因：此员工已离职",
        "",
        "请帮忙开启默认设置: Your message couldn't be delivered as the user already left organization.",
        "",
        "谢谢！",
        "",
        _signature_text()
    ])

    mail.Body = "\n".join(email_body)
    mail.Send()


def send_sap_support_email(emp_id: str, ticket_no: str, ticket_image_path: str, support_type: str = "reset_password") -> None:
    settings = get_email_settings("sap_support")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    # Map support types to subject and body text
    support_messages = {
        "password_reset": {
            "subject": f"SAP 814 Accounts Password Reset - {emp_id}",
            "message": f"Kindly approve the SAP Ticket # {ticket_no} for <strong>password reset</strong>."
        },
        "unlock_account": {
            "subject": f"SAP 814 Account Unlock Request - {emp_id}",
            "message": f"Kindly approve the SAP Ticket # {ticket_no} to <strong>unlock the account</strong>."
        },
        "role_adjustment": {
            "subject": f"SAP 814 Account Role Adjustment - {emp_id}",
            "message": f"Kindly approve the SAP Ticket # {ticket_no} for <strong>role adjustment</strong>."
        },
        "other_support": {
            "subject": f"SAP 814 Account Support Request - {emp_id}",
            "message": f"Kindly approve the SAP Ticket # {ticket_no} for account support."
        }
    }
    
    # Get the appropriate message or use default
    support_info = support_messages.get(support_type, support_messages["password_reset"])
    mail.Subject = support_info["subject"]

    html_body = [
        "<html>",
        "<body style=\"font-family: Consolas, 'Segoe UI', sans-serif; color: #0d1117;\">",
        "    <p>Hi Boss,</p>",
        f"    <p>{support_info['message']}</p>"
    ]

    if ticket_image_path and os.path.exists(ticket_image_path):
        try:
            content_id = f"ticketimg_{uuid.uuid4().hex}"
            display_name = os.path.basename(ticket_image_path)
            attachment = mail.Attachments.Add(ticket_image_path, 1, 0, display_name)
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
                content_id
            )
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3713001F",
                content_id
            )
            html_body.append(
                "    <div style=\"margin-top: 10px;\">"
                f"        <img src=\"cid:{content_id}\" alt=\"Ticket Screenshot\" style=\"max-width: 600px; height: auto; border: 1px solid #d0d7de;\">"
                "    </div>"
            )
        except Exception:
            html_body.append("    <p style=\"color: #cf222e;\">(Ticket screenshot attached)</p>")
            _attach_files(mail, [ticket_image_path])

    html_body.extend([
        f"    <p>{_signature_html()}</p>",
        "</body>",
        "</html>"
    ])

    mail.HTMLBody = "\n".join(html_body)
    mail.Send()


def send_sap_creation_email(email_attach_paths: Dict[str, Any]) -> None:
    settings = get_email_settings("sap_creation")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    employee_numbers: List[str] = email_attach_paths.get("employee_nos", [])
    emp_join = ",".join(employee_numbers)
    mail.Subject = f"SAP 814 Acc creation_{emp_join}"

    ticket_no = email_attach_paths.get('ticket_no', '')
    follow_text = email_attach_paths.get('follow_text', '')

    html_body = [
        "<p>Hi Boss,</p>",
        f"<p>Pls approve the ticket # {ticket_no}.</p>"
    ]

    ticket_image = email_attach_paths.get('ticket_image')
    if ticket_image and os.path.exists(ticket_image):
        try:
            attachment = mail.Attachments.Add(ticket_image, 1, 0, os.path.basename(ticket_image))
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F", "ticketimg"
            )
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3713001F", "ticketimg"
            )
            html_body.append('<p><img src="cid:ticketimg" alt="Ticket Image" style="max-width:600px; height:auto;"></p>')
        except Exception:
            html_body.append("<p>(Ticket image attached)</p>")
            mail.Attachments.Add(ticket_image)

    html_body.extend([
        "<p>Hi Windy,</p>",
        f"<p>Lingyun经理同意后，麻烦協助创建SAP账号，{follow_text if follow_text else ''}，細節如附件。谢谢</p>",
        f"<p>{_signature_html()}</p>"
    ])

    user_file = email_attach_paths.get('user_file')
    if user_file and os.path.exists(user_file):
        mail.Attachments.Add(user_file)

    mail.HTMLBody = "\n".join(html_body)
    mail.Send()


def send_agile_creation_email(
    users: List[Dict[str, str]],
    system_types: List[str],
    ticket_no: str,
    employee_ids: List[str],
    ticket_image: str | None,
    ticket_text: str,
) -> None:
    settings = get_email_settings("agile_creation")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    system_label = " & ".join(system_types)
    mail.Subject = (
        f"Please help to create {system_label} Agile Account for new user - {', '.join(employee_ids)}"
    )

    body_lines = [
        "<p>Hi Yang Zhong,</p>",
        f"<p>Please help to create {system_label} Agile account for below user.</p>",
        f"<p>Ticket #: {ticket_no}</p>",
    ]

    if employee_ids:
        body_lines.append("<p><strong>User List:</strong></p>")
        user_items = "".join(f"<li>{emp}</li>" for emp in employee_ids)
        body_lines.append(f"<ul>{user_items}</ul>")

    if ticket_image and os.path.exists(ticket_image):
        try:
            attachment = mail.Attachments.Add(ticket_image, 1, 0, os.path.basename(ticket_image))
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
                "ticketimg",
            )
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3713001F",
                "ticketimg",
            )
            body_lines.append('<p><img src="cid:ticketimg" alt="Ticket Screenshot" style="max-width:640px;height:auto;"></p>')
        except Exception:
            body_lines.append("<p>(Ticket screenshot attached)</p>")
            _attach_files(mail, [ticket_image])

    if ticket_text:
        body_lines.append("<p><strong>Ticket Details:</strong></p>")
        body_lines.append(
            f"<pre style=\"background:#21262d;color:#c9d1d9;padding:12px;border-radius:6px;white-space:pre-wrap;\">{ticket_text}</pre>"
        )

    body_lines.append(f"<p>{_signature_html()}</p>")

    mail.HTMLBody = "\n".join(body_lines)
    mail.Send()


def send_agile_reset_email(
    system_types: List[str],
    ticket_no: str,
    employee_id: str,
    ticket_image: str | None,
) -> None:
    settings = get_email_settings("agile_reset")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    system_label = " & ".join(system_types)
    mail.Subject = f"Please help to reset {system_label} Agile password for {employee_id}"

    body_lines = [
        "<p>Hi Yang Zhong,</p>",
        f"<p>Please help to reset {system_label} Agile account for below user.</p>",
        f"<p>Ticket #: {ticket_no}</p>",
        f"<p><strong>User:</strong> {employee_id}</p>",
    ]

    if ticket_image and os.path.exists(ticket_image):
        try:
            attachment = mail.Attachments.Add(ticket_image, 1, 0, os.path.basename(ticket_image))
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
                "ticketimg",
            )
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3713001F",
                "ticketimg",
            )
            body_lines.append('<p><img src="cid:ticketimg" alt="Ticket Screenshot" style="max-width:640px;height:auto;"></p>')
        except Exception:
            body_lines.append("<p>(Ticket screenshot attached)</p>")
            _attach_files(mail, [ticket_image])

    body_lines.append(f"<p>{_signature_html()}</p>")

    mail.HTMLBody = "\n".join(body_lines)
    mail.Send()


def send_sap_disable_email(employee_numbers: List[str], ticket_no: str, ticket_image_path: str) -> None:
    """Send email to disable SAP accounts with ticket information."""
    settings = get_email_settings("sap_disable")

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")

    # Create subject with employee numbers
    emp_join = ",".join(employee_numbers)
    mail.Subject = f"SAP 814 Acc disable_{emp_join}"

    # Build HTML email body
    html_body = [
        "<html>",
        "<body style=\"font-family: Consolas, 'Segoe UI', sans-serif; color: #0d1117;\">",
        "    <p>Hi Windy,</p>",
        "",
        f"    <p><strong>TICKET NO: {ticket_no}</strong></p>",
        "    <p>因员工离职，麻烦協助disable SAP账号，账号如下。谢谢。</p>",
        "    <p>",
    ]
    
    # Add each employee number
    for emp in employee_numbers:
        html_body.append(f"    {emp}<br>")
    
    html_body.append("    </p>")
    
    # Add ticket image if provided
    if ticket_image_path and os.path.exists(ticket_image_path):
        try:
            content_id = f"ticketimg_{uuid.uuid4().hex}"
            display_name = os.path.basename(ticket_image_path)
            attachment = mail.Attachments.Add(ticket_image_path, 1, 0, display_name)
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F",
                content_id
            )
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3713001F",
                content_id
            )
            html_body.append(
                "    <div style=\"margin-top: 10px;\">"
                f"        <img src=\"cid:{content_id}\" alt=\"Ticket Screenshot\" style=\"max-width: 600px; height: auto; border: 1px solid #d0d7de;\">"
                "    </div>"
            )
        except Exception:
            html_body.append("    <p style=\"color: #cf222e;\">(Ticket screenshot attached)</p>")
            _attach_files(mail, [ticket_image_path])
    
    html_body.extend([
        f"    <p>{_signature_html()}</p>",
        "</body>",
        "</html>"
    ])

    mail.HTMLBody = "\n".join(html_body)
    mail.Send()


def send_singtel_telco_email(sip_pdf_path: str, telco_pdf_path: str, igs32_path: str) -> None:
    """Send Singtel telco bill email with attachments."""
    from datetime import datetime
    
    settings = get_email_settings("singtel_telco")
    
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")
    
    # Get current month and year
    now = datetime.now()
    month_name = now.strftime('%b')  # Sep, Oct, etc.
    year_full = now.strftime('%Y')  # 2025
    
    mail.Subject = f"IGS Telco Bill {month_name} {year_full}"
    
    # Build email body
    email_body = [
        "Dear Team,",
        "",
        f"Please refer to attached Ingrasys {month_name} {year_full} Telco Bill, Thanks!",
        f"As a reminder, copy is available in public folder {igs32_path} as well.",
        "",
        _signature_text()
    ]
    
    mail.Body = "\n".join(email_body)
    
    # Attach both PDFs from IGS.32 path
    if sip_pdf_path and os.path.exists(sip_pdf_path):
        mail.Attachments.Add(sip_pdf_path)
    if telco_pdf_path and os.path.exists(telco_pdf_path):
        mail.Attachments.Add(telco_pdf_path)
    
    mail.Send()


def send_m1_telco_email(m1_pdf_path: str) -> None:
    """Send M1 SIM Card Plan bill email with attachment."""
    from datetime import datetime
    
    settings = get_email_settings("m1_telco")
    
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = settings.get("to", "")
    mail.CC = settings.get("cc", "")
    
    # Get current month and year
    now = datetime.now()
    month_name = now.strftime('%b')  # Sep, Oct, etc.
    year_full = now.strftime('%Y')  # 2025
    
    mail.Subject = f"IGS M1 SIM Card Plan Bill - {month_name} {year_full}"
    
    # Build email body
    email_body = [
        "Dear Team,",
        "",
        f"Please see attachment for M1 {month_name} {year_full} bill, as usual update into public shared drive as well.",
        "",
        _signature_text()
    ]
    
    mail.Body = "\n".join(email_body)
    
    # Attach M1 PDF from IGS.32 path
    if m1_pdf_path and os.path.exists(m1_pdf_path):
        mail.Attachments.Add(m1_pdf_path)
    
    mail.Send()

