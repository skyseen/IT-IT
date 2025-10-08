"""Tkinter UI components for the IT admin tool."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List

import pandas as pd

from config_manager import (
    create_profile,
    delete_profile,
    get_email_settings,
    get_active_profile_name,
    get_path,
    get_signature_text,
    list_email_sections,
    list_config_backups,
    list_profiles,
    list_paths,
    update_profile_settings,
    set_active_profile,
    set_path,
)
from activity_log import log_event
from email_service import (
    send_agile_creation_email,
    send_agile_reset_email,
    send_disable_user_email,
    send_new_user_email,
    send_sap_support_email,
    send_sap_disable_email,
    send_singtel_telco_email,
    send_m1_telco_email,
)

# Beauty-Tech Inspired Light Theme
BASE_BG = '#F9F6FB'  # Airy neutral base
PANEL_BG = '#FFFFFF'  # Clean cards and panels
INPUT_BG = '#FDF8FB'  # Soft blush input fields
ACCENT = '#8AA7FF'  # Cool tech accent
SECONDARY_ACCENT = '#D9A5B3'  # Rose-gold highlight
POSITIVE = '#7CC3A2'  # Mint confirmation tone
INFO_ACCENT = '#9E8CFF'  # Lavender info tone
WARNING = '#F4C989'  # Champagne warning tone
DANGER = '#E69896'  # Calm coral for destructive actions
TEXT_PRIMARY = '#2F2635'  # Deep plum text
TEXT_MUTED = '#6F6475'  # Muted lilac-gray secondary text
BORDER_COLOR = '#E8DBEC'  # Gentle divider
SHADOW_COLOR = '#E4D7EA'  # Diffused shadow
from user_workflow import generate_user_workbooks
from sap_workflows import (
    build_preview_window,
    get_all_existing_employees,
    parse_user_excel,
    disable_sap_accounts,
)
from telco_workflows import (
    process_singtel_bills,
    process_m1_bill,
    update_both_m1_excels,
)


def build_user_management_section(parent: tk.Widget) -> None:
    section = ttk.LabelFrame(parent, text="👥 User Management", style='MainTech.TLabelframe')
    section.pack(fill='x', pady=(0, 20))
    
    # Add subtle shadow effect with a border frame
    container = ttk.Frame(section, style='MainTech.TFrame')
    container.pack(fill='x', padx=20, pady=16)

    ttk.Button(
        container,
        text="✉ Create New User Email",
        command=lambda: build_multiuser_form(
            container.winfo_toplevel(),
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
        ),
        style='MainTechButton.TButton'
    ).pack(fill='x', pady=(0, 10))

    ttk.Button(
        container,
        text="🚫 Disable User Email Access",
        command=lambda: build_multiuser_form(
            container.winfo_toplevel(),
            "Disable User Email",
            ["User Name", "Display Name", "Employee ID"],
            handle_disable_user_email
        ),
        style='DangerButton.TButton'
    ).pack(fill='x')


def build_sap_section(parent: tk.Widget) -> None:
    section = ttk.LabelFrame(parent, text="📊 SAP Integration", style='MainTech.TLabelframe')
    section.pack(fill='x', pady=(0, 20))
    container = ttk.Frame(section, style='MainTech.TFrame')
    container.pack(fill='x', padx=20, pady=16)

    ttk.Button(
        container,
        text="🔄 Process SAP S4 Account Creation",
        command=launch_sap_flow,
        style='InfoButton.TButton'
    ).pack(fill='x', pady=(0, 10))

    ttk.Button(
        container,
        text="🛠 SAP S4 Account Support",
        command=launch_sap_support,
        style='InfoButton.TButton'
    ).pack(fill='x', pady=(0, 10))

    ttk.Button(
        container,
        text="🚫 Disable SAP S4 Account",
        command=launch_sap_disable,
        style='DangerButton.TButton'
    ).pack(fill='x')


def build_agile_section(parent: tk.Widget) -> None:
    section = ttk.LabelFrame(parent, text="⚡ Agile Integration", style='MainTech.TLabelframe')
    section.pack(fill='x', pady=(0, 20))
    container = ttk.Frame(section, style='MainTech.TFrame')
    container.pack(fill='x', padx=20, pady=16)

    ttk.Button(
        container,
        text="➕ Create Agile Account",
        command=launch_agile_creation,
        style='MainTechButton.TButton'
    ).pack(fill='x', pady=(0, 10))

    ttk.Button(
        container,
        text="🔑 Reset Agile Password",
        command=launch_agile_reset,
        style='DangerButton.TButton'
    ).pack(fill='x')


def build_multiuser_form(root: tk.Tk, title: str, labels: List[str], submit_handler: Callable[[List[Dict[str, str]]], None]) -> None:
    form = tk.Toplevel(root)
    form.title(title)
    screen_width, screen_height = form.winfo_screenwidth(), form.winfo_screenheight()
    window_width = min(max(720, int(screen_width * 0.62)), 940)
    window_height = min(max(640, int(screen_height * 0.82)), 960)
    form.geometry(f"{window_width}x{window_height}")
    form.configure(bg=BASE_BG)

    style = ttk.Style(form)
    style.configure('Tech.TFrame', background=BASE_BG, relief='flat')
    style.configure('TechPanel.TFrame', background=PANEL_BG, borderwidth=1, relief='flat')
    style.configure('Tech.TLabelframe', background=PANEL_BG, foreground=ACCENT, borderwidth=0, relief='flat', padding=20)
    style.configure('Tech.TLabelframe.Label', background=PANEL_BG, foreground=ACCENT, font=('Segoe UI', 11, 'bold'))
    style.configure('Tech.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('Tech.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, borderwidth=1, insertcolor=ACCENT, font=('Segoe UI', 10), relief='flat')
    style.configure('TechButton.TButton', background=POSITIVE, foreground='#ffffff', borderwidth=0, padding=(14, 10), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map(
        'TechButton.TButton',
        background=[('active', '#68B491'), ('pressed', '#5AA884')],
    )

    canvas = tk.Canvas(form, bg=BASE_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style='Tech.TFrame')
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)

    def on_canvas_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        if canvas.bbox("all")[3] > canvas.winfo_height():
            scrollbar.pack(side="right", fill="y")
        else:
            scrollbar.pack_forget()

    canvas.bind('<Configure>', on_canvas_configure)

    main_frame = ttk.Frame(scrollable_frame, style='Tech.TFrame', padding="28")
    main_frame.pack(fill='both', expand=True)

    title_label = tk.Label(main_frame, text=title, font=('Segoe UI', 18, 'bold'), bg=BASE_BG, fg=TEXT_PRIMARY, anchor='w')
    title_label.pack(fill='x', pady=(0, 10))
    
    # Info label for special characters
    info_label = tk.Label(main_frame, 
                         text="ℹ️ Names can include special characters (/, !, @, etc.)", 
                         font=('Segoe UI', 9), 
                         bg=BASE_BG, 
                         fg=TEXT_MUTED, 
                         anchor='w')
    info_label.pack(fill='x', pady=(0, 20))

    entries: Dict[str, tk.Entry] = {}
    for label in labels:
        field_frame = ttk.Frame(main_frame, style='TechPanel.TFrame')
        field_frame.pack(fill='x', pady=8)
        ttk.Label(field_frame, text=f"{label}:", style='Tech.TLabel', width=20, anchor='w').pack(side='left', padx=(0, 15))
        entry = ttk.Entry(field_frame, width=35, style='Tech.TEntry')
        entry.pack(side='right', fill='x', expand=True)
        entries[label] = entry

    list_frame = ttk.LabelFrame(main_frame, text="User Queue", style='Tech.TLabelframe')
    list_frame.pack(fill='both', expand=True, pady=(0, 18))
    list_scroll = ttk.Scrollbar(list_frame)
    list_scroll.pack(side='right', fill='y')
    listbox = tk.Listbox(list_frame, font=('Segoe UI', 10), bg=INPUT_BG, fg=TEXT_PRIMARY, height=9, selectbackground=ACCENT, selectforeground='#ffffff', borderwidth=0, highlightthickness=0, relief='flat')
    listbox.pack(side='left', fill='both', expand=True)
    listbox.config(yscrollcommand=list_scroll.set)
    list_scroll.config(command=listbox.yview)

    user_list: List[Dict[str, str]] = []

    def _refresh_listbox() -> None:
        listbox.delete(0, 'end')
        for idx, data in enumerate(user_list, start=1):
            display_name = data.get('Display Name', '')
            listbox.insert('end', f"[{idx:02d}] {data[labels[0]]} → {display_name}")

    def add_user() -> None:
        data = {label: entries[label].get().strip() for label in labels}
        if all(data.values()):
            user_list.append(data)
            _refresh_listbox()
            for entry in entries.values():
                entry.delete(0, 'end')
            entries[labels[0]].focus()
        else:
            messagebox.showerror("INPUT_ERROR", "All fields must be filled before adding user.", parent=form)

    def remove_user() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("SELECTION_ERROR", "Select a user to remove.", parent=form)
            return
        index = selection[0]
        user_list.pop(index)
        _refresh_listbox()
        if user_list:
            listbox.selection_set(min(index, len(user_list) - 1))

    def submit_all() -> None:
        if not user_list:
            messagebox.showerror("QUEUE_EMPTY", "No users in queue! Add users before submitting.", parent=form)
            return

        confirm = messagebox.askyesno(
            "EXECUTE_BATCH",
            f"Execute batch operation for {len(user_list)} user(s)?\n\nThis action cannot be undone.",
            parent=form,
        )
        if not confirm:
            return

        submit_handler(user_list)
        form.destroy()

    control_frame = ttk.Frame(main_frame, style='TechPanel.TFrame')
    control_frame.pack(fill='x', pady=(0, 15))
    ttk.Button(control_frame, text="➕ Add User", style='TechButton.TButton', command=add_user).pack(side='left', padx=(0, 10), expand=True, fill='x')
    ttk.Button(control_frame, text="➖ Remove Selected", style='TechButton.TButton', command=remove_user).pack(side='left', padx=(10, 0), expand=True, fill='x')
    ttk.Button(main_frame, text="✅ Submit All", style='TechButton.TButton', command=submit_all).pack(fill='x', pady=10)
    entries[labels[0]].focus()


def handle_new_user_email(user_list: List[Dict[str, str]]) -> None:
    log_event(
        "user.onboarding",
        "Preparing new user onboarding email run",
        details={"count": len(user_list)},
    )

    save_folder = get_path("new_user_save_folder")
    if not save_folder:
        selected = filedialog.askdirectory(title="Select folder to save new user templates")
        if not selected:
            messagebox.showerror("INPUT_ERROR", "Save folder is required to generate templates.")
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
    except Exception as exc:
        log_event(
            "user.onboarding",
            "New user email workflow failed",
            level="error",
            details={"error": str(exc)},
        )
        messagebox.showerror(
            "ERROR",
            f"Unable to prepare and send the new user email.\n\nDetails: {exc}",
        )
        return

    log_event(
        "user.onboarding",
        "New user email dispatched",
        details={"count": len(user_list), "attachments": len(attachments)},
    )
    messagebox.showinfo("Success", f"New user email sent with {len(attachments)} attachments.")


def handle_disable_user_email(user_list: List[Dict[str, str]]) -> None:
    try:
        send_disable_user_email(user_list)
    except Exception as exc:
        log_event(
            "user.offboarding",
            "Disable user email workflow failed",
            level="error",
            details={"error": str(exc), "count": len(user_list)},
        )
        messagebox.showerror(
            "ERROR",
            f"Unable to complete disable user email workflow.\n\nDetails: {exc}",
        )
        return

    log_event(
        "user.offboarding",
        "Disable user email dispatched",
        details={"count": len(user_list)},
    )
    messagebox.showinfo("Success", "Disable user email sent successfully.")


def launch_sap_flow():
    user_excel_path = filedialog.askopenfilename(
        title="Select user-submitted SAP Excel",
        filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")],
    )
    if not user_excel_path:
        log_event("sap.creation", "SAP creation flow cancelled - no Excel selected", level="warning")
        return

    try:
        user_df = pd.read_excel(user_excel_path, engine="openpyxl")
    except Exception as exc:
        log_event(
            "sap.creation",
            "Unable to read user submitted SAP Excel",
            level="error",
            details={"error": str(exc), "file": user_excel_path},
        )
        messagebox.showerror(
            "ERROR",
            f"Failed to read the user submitted Excel.\n\nDetails: {exc}",
        )
        return

    cons_path = get_path("consolidated_excel")
    if not cons_path or not os.path.exists(cons_path):
        cons_path = filedialog.askopenfilename(
            title="Select Consolidated SAP Excel",
            filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")],
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

    try:
        existing_emp = get_all_existing_employees(cons_path)
        parsed = parse_user_excel(user_df, existing_emp)
    except Exception as exc:
        log_event(
            "sap.creation",
            "Failed to parse SAP onboarding workbook",
            level="error",
            details={"error": str(exc)},
        )
        messagebox.showerror("ERROR", f"Unable to parse SAP onboarding Excel.\n\nDetails: {exc}")
        return

    if not parsed.rows_to_append and not parsed.already_created:
        log_event(
            "sap.creation",
            "SAP onboarding workbook contained no actionable rows",
            level="warning",
        )
        messagebox.showinfo("Nothing to process", "No valid employees found.")
        return

    log_event(
        "sap.creation",
        "Launching SAP onboarding preview",
        details={"pending_rows": len(parsed.rows_to_append)},
    )
    build_preview_window(
        parsed.rows_to_append,
        parsed.already_created,
        cons_path,
        user_excel_path,
        parsed.other_desc_map,
    )


def launch_sap_support():
    support_window = tk.Toplevel()
    support_window.title("SAP_S4_ACCOUNT_SUPPORT")
    support_window.configure(bg=BASE_BG)
    support_window.geometry("700x650")

    style = ttk.Style(support_window)
    style.configure('Support.TFrame', background=BASE_BG, relief='flat')
    style.configure('SupportPanel.TFrame', background=PANEL_BG, relief='flat')
    style.configure('Support.TLabelframe', background=PANEL_BG, foreground=ACCENT, borderwidth=0, relief='flat', padding=20)
    style.configure('Support.TLabelframe.Label', background=PANEL_BG, foreground=ACCENT, font=('Segoe UI', 11, 'bold'))
    style.configure('Support.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('Support.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=ACCENT, font=('Segoe UI', 10), borderwidth=1, relief='flat')
    style.configure('SupportButton.TButton', background=POSITIVE, foreground='#ffffff', padding=(14, 10), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map(
        'SupportButton.TButton',
        background=[('active', '#68B491'), ('pressed', '#5AA884')],
    )

    canvas = tk.Canvas(support_window, bg=BASE_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(support_window, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style='Support.TFrame')
    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side='left', fill='both', expand=True)

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox('all'))
        if canvas.bbox('all') and canvas.bbox('all')[3] > canvas.winfo_height():
            scrollbar.pack(side='right', fill='y')
        else:
            scrollbar.pack_forget()

    canvas.bind('<Configure>', on_configure)

    main_frame = ttk.Frame(scrollable_frame, style='Support.TFrame', padding=32)
    main_frame.pack(fill='both', expand=True)

    header = ttk.Frame(main_frame, style='Support.TFrame')
    header.pack(fill='x', pady=(0, 25))
    tk.Label(header, text='🛠 SAP S4 Account Support', font=('Segoe UI', 18, 'bold'), bg=BASE_BG, fg=TEXT_PRIMARY, anchor='w').pack(fill='x')
    tk.Label(header, text='Select support type and provide required information', font=('Segoe UI', 10), bg=BASE_BG, fg=TEXT_MUTED, anchor='w').pack(fill='x', pady=(8, 0))

    support_type_var = tk.StringVar(value='reset_password')

    type_frame = ttk.LabelFrame(main_frame, text='Support Type', style='Support.TLabelframe')
    type_frame.pack(fill='x', pady=(0, 20))
    type_inner = ttk.Frame(type_frame, style='Support.TFrame')
    type_inner.pack(fill='x', padx=10, pady=10)

    tk.Radiobutton(type_inner, text='Reset Password', variable=support_type_var, value='reset_password', font=('Segoe UI', 10), bg=PANEL_BG, fg=TEXT_PRIMARY, selectcolor=INPUT_BG, activebackground=PANEL_BG, activeforeground=ACCENT).pack(anchor='w', pady=4)
    tk.Radiobutton(type_inner, text='Reactivate Account (Coming Soon)', variable=support_type_var, value='reactivate', state='disabled', font=('Segoe UI', 10), bg=PANEL_BG, fg=TEXT_MUTED, selectcolor=INPUT_BG).pack(anchor='w', pady=4)

    info_frame = ttk.LabelFrame(main_frame, text='Required Information', style='Support.TLabelframe')
    info_frame.pack(fill='x', pady=(0, 20))
    info_inner = ttk.Frame(info_frame, style='Support.TFrame')
    info_inner.pack(fill='x', padx=15, pady=15)

    emp_id_var = tk.StringVar()
    ticket_no_var = tk.StringVar()
    screenshot_var = tk.StringVar()

    def _build_labeled_entry(parent: ttk.Frame, label: str, text_var: tk.StringVar) -> ttk.Entry:
        row = ttk.Frame(parent, style='Support.TFrame')
        row.pack(fill='x', pady=8)
        ttk.Label(row, text=label, style='Support.TLabel', width=14, anchor='w').pack(side='left')
        entry = ttk.Entry(row, textvariable=text_var, style='Support.TEntry')
        entry.pack(side='right', fill='x', expand=True)
        return entry

    emp_entry = _build_labeled_entry(info_inner, 'EMPLOYEE ID', emp_id_var)
    ticket_entry = _build_labeled_entry(info_inner, 'TICKET NO', ticket_no_var)

    screenshot_frame = ttk.LabelFrame(main_frame, text='TICKET_SCREENSHOT', style='Support.TLabelframe')
    screenshot_frame.pack(fill='x', pady=(0, 22))
    screenshot_inner = ttk.Frame(screenshot_frame, style='SupportPanel.TFrame')
    screenshot_inner.pack(fill='x', padx=18, pady=12)

    screenshot_label = ttk.Label(screenshot_inner, text='No file selected', style='Support.TLabel')
    screenshot_label.pack(fill='x', pady=(0, 10))

    def select_screenshot() -> None:
        dialog_kwargs = {
            'title': 'Select Ticket Screenshot',
            'filetypes': [('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')],
        }
        default_dir = get_path('sap_ticket_image_dir')
        if default_dir and os.path.isdir(default_dir):
            dialog_kwargs['initialdir'] = default_dir

        file_path = filedialog.askopenfilename(parent=support_window, **dialog_kwargs)
        if file_path:
            screenshot_var.set(file_path)
            screenshot_label.config(text=f'Selected: {os.path.basename(file_path)}')
            set_path('sap_ticket_image_dir', os.path.dirname(file_path))

    ttk.Button(screenshot_inner, text='[SELECT] SCREENSHOT', style='SupportButton.TButton', command=select_screenshot).pack(fill='x')

    def submit_support() -> None:
        emp_id = emp_id_var.get().strip()
        ticket_no = ticket_no_var.get().strip()
        screenshot_path = screenshot_var.get().strip()

        if not emp_id:
            messagebox.showerror('INPUT_ERROR', 'Employee ID is required.', parent=support_window)
            emp_entry.focus_set()
            return
        if not ticket_no:
            messagebox.showerror('INPUT_ERROR', 'Ticket number is required.', parent=support_window)
            ticket_entry.focus_set()
            return
        if not screenshot_path:
            messagebox.showerror('INPUT_ERROR', 'Ticket screenshot is required.', parent=support_window)
            return
        if not os.path.exists(screenshot_path):
            messagebox.showerror('INPUT_ERROR', 'Selected screenshot file could not be found.', parent=support_window)
            return

        confirm = messagebox.askyesno(
            'CONFIRM_SUBMISSION',
            f'Proceed with submitting support request for {emp_id}?\n\nTicket: {ticket_no}\nSupport Type: {support_type_var.get().replace("_", " ").title()}',
            parent=support_window,
        )
        if not confirm:
            return

        try:
            send_sap_support_email(emp_id, ticket_no, screenshot_path, support_type_var.get())
        except Exception as exc:
            log_event(
                "sap.support",
                "SAP support email failed",
                level="error",
                details={"error": str(exc), "employee": emp_id, "ticket": ticket_no},
            )
            messagebox.showerror(
                'ERROR',
                f'Failed to send SAP support email.\n\nDetails: {exc}',
                parent=support_window,
            )
            return

        log_event(
            "sap.support",
            "SAP support email dispatched",
            details={"employee": emp_id, "ticket": ticket_no},
        )
        messagebox.showinfo('SUCCESS', f'Support email sent for {emp_id}.', parent=support_window)
        support_window.destroy()

    ttk.Button(main_frame, text='[EXECUTE] SUBMIT_SUPPORT_REQUEST', style='SupportButton.TButton', command=submit_support).pack(fill='x', pady=(12, 0))

    emp_entry.focus_set()
    support_window.grab_set()
    support_window.bind('<Escape>', lambda _e: support_window.destroy())


def launch_sap_disable():
    """Launch SAP S4 Account Disable workflow."""
    disable_window = tk.Toplevel()
    disable_window.title("SAP_S4_ACCOUNT_DISABLE")
    disable_window.configure(bg=BASE_BG)
    disable_window.geometry("700x500")

    style = ttk.Style(disable_window)
    style.configure('Disable.TFrame', background=BASE_BG, relief='flat')
    style.configure('DisablePanel.TFrame', background=PANEL_BG, relief='flat')
    style.configure('Disable.TLabelframe', background=PANEL_BG, foreground=DANGER, borderwidth=0, relief='flat', padding=20)
    style.configure('Disable.TLabelframe.Label', background=PANEL_BG, foreground=DANGER, font=('Segoe UI', 11, 'bold'))
    style.configure('Disable.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('Disable.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=ACCENT, font=('Segoe UI', 10), borderwidth=1, relief='flat')
    style.configure('DisableButton.TButton', background=DANGER, foreground='#ffffff', padding=(14, 10), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map(
        'DisableButton.TButton',
        background=[('active', '#D07A77'), ('pressed', '#C06764')],
    )

    canvas = tk.Canvas(disable_window, bg=BASE_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(disable_window, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style='Disable.TFrame')
    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side='left', fill='both', expand=True)

    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox('all'))
        if canvas.bbox('all') and canvas.bbox('all')[3] > canvas.winfo_height():
            scrollbar.pack(side='right', fill='y')
        else:
            scrollbar.pack_forget()

    canvas.bind('<Configure>', on_configure)

    main_frame = ttk.Frame(scrollable_frame, style='Disable.TFrame', padding=32)
    main_frame.pack(fill='both', expand=True)

    header = ttk.Frame(main_frame, style='Disable.TFrame')
    header.pack(fill='x', pady=(0, 25))
    tk.Label(header, text='🚫 Disable SAP S4 Account', font=('Segoe UI', 18, 'bold'), bg=BASE_BG, fg=TEXT_PRIMARY, anchor='w').pack(fill='x')
    tk.Label(header, text='Enter employee numbers to disable SAP accounts', font=('Segoe UI', 10), bg=BASE_BG, fg=TEXT_MUTED, anchor='w').pack(fill='x', pady=(8, 0))

    employees_frame = ttk.LabelFrame(main_frame, text='Employee Numbers', style='Disable.TLabelframe')
    employees_frame.pack(fill='both', expand=True, pady=(0, 20))
    employees_inner = ttk.Frame(employees_frame, style='Disable.TFrame')
    employees_inner.pack(fill='both', expand=True, padx=15, pady=10)

    employee_var = tk.StringVar()
    ttk.Label(employees_inner, text='Employee ID', style='Disable.TLabel').grid(row=0, column=0, sticky='w')
    employee_entry = ttk.Entry(employees_inner, textvariable=employee_var, style='Disable.TEntry')
    employee_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))
    add_button = ttk.Button(employees_inner, text='+ Add', style='DisableButton.TButton')
    add_button.grid(row=0, column=2, padx=(10, 0))

    employees_inner.columnconfigure(1, weight=1)

    listbox = tk.Listbox(
        employees_inner,
        font=('Segoe UI', 10),
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        selectbackground=DANGER,
        selectforeground='#ffffff',
        height=8,
        borderwidth=0,
        highlightthickness=0,
        relief='flat'
    )
    listbox.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=(10, 0))
    employees_inner.rowconfigure(1, weight=1)

    remove_button = ttk.Button(employees_inner, text='− Remove Selected', style='DisableButton.TButton')
    remove_button.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(10, 0))

    employees: List[str] = []

    def refresh_employee_list() -> None:
        listbox.delete(0, 'end')
        for idx, emp in enumerate(employees, start=1):
            listbox.insert('end', f"[{idx:02d}] {emp}")

    def add_employee() -> None:
        value = employee_var.get().strip()
        if not value:
            messagebox.showerror('INPUT_ERROR', 'Employee ID is required before adding.', parent=disable_window)
            return
        employees.append(value)
        refresh_employee_list()
        employee_var.set('')
        employee_entry.focus_set()

    def remove_employee() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror('SELECTION_ERROR', 'Select an employee to remove.', parent=disable_window)
            return
        index = selection[0]
        employees.pop(index)
        refresh_employee_list()

    add_button.configure(command=add_employee)
    remove_button.configure(command=remove_employee)

    def submit_disable() -> None:
        if not employees:
            messagebox.showerror('INPUT_ERROR', 'Add at least one employee ID.', parent=disable_window)
            return

        log_event(
            "sap.disable",
            "Preparing SAP disable workflow",
            details={"count": len(employees)},
        )

        # Get consolidated Excel path
        cons_path = get_path("consolidated_excel")
        if not cons_path or not os.path.exists(cons_path):
            cons_path = filedialog.askopenfilename(
                parent=disable_window,
                title="Select Consolidated SAP Excel",
                filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
            )
            if not cons_path:
                return
            set_path("consolidated_excel", cons_path)

        confirm = messagebox.askyesno(
            'CONFIRM_DISABLE',
            f'Disable SAP accounts for {len(employees)} employee(s)?\n\n'
            f'Employee IDs: {", ".join(employees)}\n\n'
            f'This will mark the STATUS column as "Disabled" in the consolidated Excel.',
            parent=disable_window,
        )
        if not confirm:
            log_event(
                "sap.disable",
                "SAP disable workflow cancelled at confirmation",
                level='warning',
                details={"count": len(employees)},
            )
            return

        try:
            # Disable accounts
            result = disable_sap_accounts(cons_path, employees)

            log_event(
                "sap.disable",
                "SAP accounts updated in consolidated workbook",
                details={
                    "updated": len(result.updated),
                    "not_found": len(result.not_found),
                },
            )

            # Show result summary
            summary_lines = []
            if result.updated:
                summary_lines.append(f"✅ UPDATED ({len(result.updated)}):")
                summary_lines.extend([f"  • {emp}" for emp in result.updated])
            
            if result.not_found:
                summary_lines.append(f"\n❌ NOT FOUND ({len(result.not_found)}):")
                summary_lines.extend([f"  • {emp}" for emp in result.not_found])
            
            summary_lines.append(f"\nTotal Updated: {len(result.updated)}")
            summary_lines.append(f"Not in List: {len(result.not_found)}")

            messagebox.showinfo(
                'DISABLE_RESULT',
                '\n'.join(summary_lines),
                parent=disable_window
            )

            # Send email only for successfully updated accounts
            if result.updated:
                # Prompt for ticket number
                from tkinter import simpledialog
                ticket_no = simpledialog.askstring(
                    "Ticket Number",
                    "Enter ticket number (e.g. SAA122212):", 
                    parent=disable_window
                )
                if not ticket_no:
                    messagebox.showwarning('CANCELLED', 'Ticket number is required. Email not sent.', parent=disable_window)
                    disable_window.destroy()
                    return
                
                # Prompt for ticket image
                dialog_kwargs = {
                    'title': 'Select Ticket Image File',
                    'filetypes': [('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')],
                }
                default_ticket_dir = get_path('sap_ticket_image_dir')
                if default_ticket_dir and os.path.isdir(default_ticket_dir):
                    dialog_kwargs['initialdir'] = default_ticket_dir

                ticket_img_path = filedialog.askopenfilename(parent=disable_window, **dialog_kwargs)
                if not ticket_img_path:
                    messagebox.showwarning('CANCELLED', 'Ticket image is required. Email not sent.', parent=disable_window)
                    disable_window.destroy()
                    return
                
                set_path('sap_ticket_image_dir', os.path.dirname(ticket_img_path))

                # Send email with ticket info
                try:
                    send_sap_disable_email(result.updated, ticket_no, ticket_img_path)
                except Exception as exc:
                    log_event(
                        "sap.disable",
                        "Failed to dispatch SAP disable email",
                        level='error',
                        details={"error": str(exc), "ticket": ticket_no},
                    )
                    messagebox.showerror(
                        'ERROR',
                        f'Failed to send disable confirmation email.\n\nDetails: {exc}',
                        parent=disable_window,
                    )
                    disable_window.destroy()
                    return

                log_event(
                    "sap.disable",
                    "SAP disable email dispatched",
                    details={"ticket": ticket_no, "count": len(result.updated)},
                )
                messagebox.showinfo('SUCCESS', 'Disable email sent successfully.', parent=disable_window)

            disable_window.destroy()

        except PermissionError:
            log_event(
                "sap.disable",
                "Consolidated Excel locked during disable workflow",
                level='error',
                details={"file": cons_path},
            )
            messagebox.showerror(
                'FILE_LOCKED',
                f'Cannot save to consolidated Excel file.\n\n'
                f'Please close the file in Excel and try again.\n\n'
                f'File: {cons_path}',
                parent=disable_window
            )
        except Exception as e:
            log_event(
                "sap.disable",
                "SAP disable workflow failed",
                level='error',
                details={"error": str(e)},
            )
            messagebox.showerror(
                'ERROR',
                f'Error disabling accounts:\n\n{str(e)}',
                parent=disable_window
            )

    ttk.Button(main_frame, text='[EXECUTE] DISABLE_ACCOUNTS', style='DisableButton.TButton', command=submit_disable).pack(fill='x')

    employee_entry.focus_set()
    disable_window.grab_set()
    disable_window.bind('<Escape>', lambda _e: disable_window.destroy())


def launch_agile_creation() -> None:
    window = tk.Toplevel()
    window.title("Agile Account Creation")
    window.configure(bg=BASE_BG)
    window.geometry("750x750")

    style = ttk.Style(window)
    style.configure('Agile.TFrame', background=BASE_BG, relief='flat')
    style.configure('Agile.TLabelframe', background=PANEL_BG, foreground=ACCENT, borderwidth=0, relief='flat', padding=20)
    style.configure('Agile.TLabelframe.Label', background=PANEL_BG, foreground=ACCENT, font=('Segoe UI', 11, 'bold'))
    style.configure('Agile.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('Agile.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=ACCENT, font=('Segoe UI', 10), borderwidth=1, relief='flat')
    style.configure('AgileButton.TButton', background=POSITIVE, foreground='#ffffff', padding=(14, 10), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map(
        'AgileButton.TButton',
        background=[('active', '#68B491'), ('pressed', '#5AA884')],
    )

    canvas = tk.Canvas(window, bg=BASE_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(window, orient='vertical', command=canvas.yview)
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    main_frame = ttk.Frame(canvas, style='Agile.TFrame', padding=30)
    canvas.create_window((0, 0), window=main_frame, anchor='nw')
    main_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.configure(yscrollcommand=scrollbar.set)

    header = ttk.Frame(main_frame, style='Agile.TFrame')
    header.pack(fill='x', pady=(0, 25))
    tk.Label(header, text='⚡ Agile Account Creation', font=('Segoe UI', 18, 'bold'), bg=BASE_BG, fg=TEXT_PRIMARY, anchor='w').pack(fill='x')
    tk.Label(header, text='Select system(s) and provide ticket details', font=('Segoe UI', 10), bg=BASE_BG, fg=TEXT_MUTED, anchor='w').pack(fill='x', pady=(8, 0))

    system_frame = ttk.LabelFrame(main_frame, text='System Selection', style='Agile.TLabelframe')
    system_frame.pack(fill='x', pady=(0, 20))
    system_inner = ttk.Frame(system_frame, style='Agile.TFrame')
    system_inner.pack(fill='x', padx=15, pady=10)

    system_vars = {
        'MFG': tk.BooleanVar(value=True),
        'RD': tk.BooleanVar(value=False)
    }

    for label, var in system_vars.items():
        tk.Checkbutton(
            system_inner,
            text=f'{label} Agile',
            variable=var,
            font=('Segoe UI', 10),
            bg=PANEL_BG,
            fg=TEXT_PRIMARY,
            selectcolor=INPUT_BG,
            activebackground=PANEL_BG,
            activeforeground=ACCENT
        ).pack(anchor='w', pady=4)

    ticket_frame = ttk.LabelFrame(main_frame, text='Ticket Information', style='Agile.TLabelframe')
    ticket_frame.pack(fill='x', pady=(0, 20))
    ticket_inner = ttk.Frame(ticket_frame, style='Agile.TFrame')
    ticket_inner.pack(fill='x', padx=15, pady=10)

    ticket_no_var = tk.StringVar()
    ttk.Label(ticket_inner, text='Ticket Number', style='Agile.TLabel').grid(row=0, column=0, sticky='w')
    ticket_entry = ttk.Entry(ticket_inner, textvariable=ticket_no_var, style='Agile.TEntry')
    ticket_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))
    ticket_inner.columnconfigure(1, weight=1)

    employees_frame = ttk.LabelFrame(main_frame, text='User Queue', style='Agile.TLabelframe')
    employees_frame.pack(fill='both', expand=True, pady=(0, 20))
    employees_inner = ttk.Frame(employees_frame, style='Agile.TFrame')
    employees_inner.pack(fill='both', expand=True, padx=15, pady=10)

    employee_var = tk.StringVar()
    ttk.Label(employees_inner, text='Employee ID', style='Agile.TLabel').grid(row=0, column=0, sticky='w')
    employee_entry = ttk.Entry(employees_inner, textvariable=employee_var, style='Agile.TEntry')
    employee_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))
    add_button = ttk.Button(employees_inner, text='+ Add', style='AgileButton.TButton')
    add_button.grid(row=0, column=2, padx=(10, 0))

    employees_inner.columnconfigure(1, weight=1)

    listbox = tk.Listbox(
        employees_inner,
        font=('Segoe UI', 10),
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        selectbackground=ACCENT,
        selectforeground='#ffffff',
        height=6,
        borderwidth=0,
        highlightthickness=0,
        relief='flat'
    )
    listbox.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=(10, 0))
    employees_inner.rowconfigure(1, weight=1)

    remove_button = ttk.Button(employees_inner, text='− Remove Selected', style='AgileButton.TButton')
    remove_button.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(10, 0))

    employees: List[str] = []

    def refresh_employee_list() -> None:
        listbox.delete(0, 'end')
        for idx, emp in enumerate(employees, start=1):
            listbox.insert('end', f"[{idx:02d}] {emp}")

    def add_employee() -> None:
        value = employee_var.get().strip()
        if not value:
            messagebox.showerror('INPUT_ERROR', 'Employee ID is required before adding.', parent=window)
            return
        employees.append(value)
        refresh_employee_list()
        employee_var.set('')
        employee_entry.focus_set()

    def remove_employee() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror('SELECTION_ERROR', 'Select an employee to remove.', parent=window)
            return
        index = selection[0]
        employees.pop(index)
        refresh_employee_list()

    add_button.configure(command=add_employee)
    remove_button.configure(command=remove_employee)

    screenshot_var = tk.StringVar()
    screenshot_frame = ttk.LabelFrame(main_frame, text='Ticket Screenshot', style='Agile.TLabelframe')
    screenshot_frame.pack(fill='x', pady=(0, 20))
    screenshot_inner = ttk.Frame(screenshot_frame, style='Agile.TFrame')
    screenshot_inner.pack(fill='x', padx=15, pady=10)

    screenshot_label = ttk.Label(screenshot_inner, text='No file selected', style='Agile.TLabel')
    screenshot_label.pack(fill='x', pady=(0, 8))

    def select_screenshot() -> None:
        dialog_kwargs = {
            'title': 'Select Ticket Screenshot',
            'filetypes': [('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')],
        }
        default_dir = get_path('agile_ticket_image_dir')
        if default_dir and os.path.isdir(default_dir):
            dialog_kwargs['initialdir'] = default_dir

        file_path = filedialog.askopenfilename(parent=window, **dialog_kwargs)
        if file_path:
            screenshot_var.set(file_path)
            screenshot_label.config(text=f'Selected: {os.path.basename(file_path)}')
            set_path('agile_ticket_image_dir', os.path.dirname(file_path))

    ttk.Button(screenshot_inner, text='📎 Select Screenshot', style='AgileButton.TButton', command=select_screenshot).pack(fill='x')

    ticket_text_frame = ttk.LabelFrame(main_frame, text='Ticket Content', style='Agile.TLabelframe')
    ticket_text_frame.pack(fill='both', expand=True, pady=(0, 20))
    ticket_text_inner = ttk.Frame(ticket_text_frame, style='Agile.TFrame')
    ticket_text_inner.pack(fill='both', expand=True, padx=15, pady=10)

    ticket_text_widget = tk.Text(
        ticket_text_inner,
        height=8,
        font=('Segoe UI', 10),
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        insertbackground=ACCENT,
        borderwidth=0,
        relief='flat',
        wrap='word',
        padx=10,
        pady=10
    )
    ticket_text_widget.pack(fill='both', expand=True)

    def submit() -> None:
        selected_systems = [label for label, var in system_vars.items() if var.get()]
        if not selected_systems:
            messagebox.showerror('INPUT_ERROR', 'Select at least one Agile system.', parent=window)
            return

        if not ticket_no_var.get().strip():
            messagebox.showerror('INPUT_ERROR', 'Ticket number is required.', parent=window)
            ticket_entry.focus_set()
            return

        if not employees:
            messagebox.showerror('INPUT_ERROR', 'Add at least one employee ID.', parent=window)
            return

        screenshot_path = screenshot_var.get().strip()
        if not screenshot_path:
            messagebox.showerror('INPUT_ERROR', 'Ticket screenshot is required.', parent=window)
            return
        if not os.path.exists(screenshot_path):
            messagebox.showerror('INPUT_ERROR', 'Selected screenshot file could not be found.', parent=window)
            return

        ticket_text = ticket_text_widget.get('1.0', 'end').strip()
        if not ticket_text:
            messagebox.showerror('INPUT_ERROR', 'Paste the ticket content into the form.', parent=window)
            return

        log_event(
            "agile.creation",
            "Preparing Agile account creation email",
            details={"systems": selected_systems, "count": len(employees)},
        )

        try:
            send_agile_creation_email(
                [{'Employee ID': emp} for emp in employees],
                selected_systems,
                ticket_no_var.get().strip(),
                employees,
                screenshot_path,
                ticket_text,
            )
        except Exception as exc:
            log_event(
                "agile.creation",
                "Agile account creation email failed",
                level='error',
                details={"error": str(exc), "ticket": ticket_no_var.get().strip()},
            )
            messagebox.showerror(
                'ERROR',
                f'Failed to prepare Agile account creation email.\n\nDetails: {exc}',
                parent=window,
            )
            return

        log_event(
            "agile.creation",
            "Agile account creation email prepared",
            details={"ticket": ticket_no_var.get().strip(), "count": len(employees)},
        )
        messagebox.showinfo('SUCCESS', 'Agile account creation email prepared and sent.', parent=window)
        window.destroy()

    ttk.Button(main_frame, text='[EXECUTE] SEND_REQUEST', style='AgileButton.TButton', command=submit).pack(fill='x')

    employee_entry.focus_set()
    parent = window.master
    if parent:
        window.transient(parent)
    window.grab_set()
    window.bind('<Escape>', lambda _e: window.destroy())


def launch_agile_reset() -> None:
    window = tk.Toplevel()
    window.title("Agile Password Reset")
    window.configure(bg=BASE_BG)
    window.geometry("680x620")

    style = ttk.Style(window)
    style.configure('AgileReset.TFrame', background=BASE_BG, relief='flat')
    style.configure('AgileReset.TLabelframe', background=PANEL_BG, foreground=ACCENT, borderwidth=0, relief='flat', padding=20)
    style.configure('AgileReset.TLabelframe.Label', background=PANEL_BG, foreground=ACCENT, font=('Segoe UI', 11, 'bold'))
    style.configure('AgileReset.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('AgileReset.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=ACCENT, font=('Segoe UI', 10), borderwidth=1, relief='flat')
    style.configure('AgileResetButton.TButton', background=DANGER, foreground='#ffffff', padding=(14, 10), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map(
        'AgileResetButton.TButton',
        background=[('active', '#D07A77'), ('pressed', '#C06764')],
    )

    canvas = tk.Canvas(window, bg=BASE_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(window, orient='vertical', command=canvas.yview)
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')

    main_frame = ttk.Frame(canvas, style='AgileReset.TFrame', padding=30)
    canvas.create_window((0, 0), window=main_frame, anchor='nw')
    main_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.configure(yscrollcommand=scrollbar.set)

    header = ttk.Frame(main_frame, style='AgileReset.TFrame')
    header.pack(fill='x', pady=(0, 25))
    tk.Label(header, text='🔑 Agile Password Reset', font=('Segoe UI', 18, 'bold'), bg=BASE_BG, fg=TEXT_PRIMARY, anchor='w').pack(fill='x')
    tk.Label(header, text='Provide ticket and user information', font=('Segoe UI', 10), bg=BASE_BG, fg=TEXT_MUTED, anchor='w').pack(fill='x', pady=(8, 0))

    system_frame = ttk.LabelFrame(main_frame, text='System Selection', style='AgileReset.TLabelframe')
    system_frame.pack(fill='x', pady=(0, 20))
    system_inner = ttk.Frame(system_frame, style='AgileReset.TFrame')
    system_inner.pack(fill='x', padx=15, pady=10)

    system_vars = {
        'MFG': tk.BooleanVar(value=True),
        'RD': tk.BooleanVar(value=False)
    }

    for label, var in system_vars.items():
        tk.Checkbutton(
            system_inner,
            text=f'{label} Agile',
            variable=var,
            font=('Segoe UI', 10),
            bg=PANEL_BG,
            fg=TEXT_PRIMARY,
            selectcolor=INPUT_BG,
            activebackground=PANEL_BG,
            activeforeground=ACCENT
        ).pack(anchor='w', pady=4)

    info_frame = ttk.LabelFrame(main_frame, text='Request Details', style='AgileReset.TLabelframe')
    info_frame.pack(fill='x', pady=(0, 20))
    info_inner = ttk.Frame(info_frame, style='AgileReset.TFrame')
    info_inner.pack(fill='x', padx=15, pady=10)

    ticket_no_var = tk.StringVar()
    emp_id_var = tk.StringVar()

    ttk.Label(info_inner, text='Ticket Number', style='AgileReset.TLabel').grid(row=0, column=0, sticky='w')
    ticket_entry = ttk.Entry(info_inner, textvariable=ticket_no_var, style='AgileReset.TEntry')
    ticket_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

    ttk.Label(info_inner, text='Employee ID', style='AgileReset.TLabel').grid(row=1, column=0, sticky='w', pady=(10, 0))
    emp_entry = ttk.Entry(info_inner, textvariable=emp_id_var, style='AgileReset.TEntry')
    emp_entry.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=(10, 0))

    info_inner.columnconfigure(1, weight=1)

    screenshot_var = tk.StringVar()
    screenshot_frame = ttk.LabelFrame(main_frame, text='Ticket Screenshot', style='AgileReset.TLabelframe')
    screenshot_frame.pack(fill='x', pady=(0, 20))
    screenshot_inner = ttk.Frame(screenshot_frame, style='AgileReset.TFrame')
    screenshot_inner.pack(fill='x', padx=15, pady=10)

    screenshot_label = ttk.Label(screenshot_inner, text='No file selected', style='AgileReset.TLabel')
    screenshot_label.pack(fill='x', pady=(0, 8))

    def select_screenshot() -> None:
        dialog_kwargs = {
            'title': 'Select Ticket Screenshot',
            'filetypes': [('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')],
        }
        default_dir = get_path('agile_ticket_image_dir')
        if default_dir and os.path.isdir(default_dir):
            dialog_kwargs['initialdir'] = default_dir

        file_path = filedialog.askopenfilename(parent=window, **dialog_kwargs)
        if file_path:
            screenshot_var.set(file_path)
            screenshot_label.config(text=f'Selected: {os.path.basename(file_path)}')
            set_path('agile_ticket_image_dir', os.path.dirname(file_path))

    ttk.Button(screenshot_inner, text='📎 Select Screenshot', style='AgileResetButton.TButton', command=select_screenshot).pack(fill='x')

    def submit() -> None:
        selected_systems = [label for label, var in system_vars.items() if var.get()]
        if not selected_systems:
            messagebox.showerror('INPUT_ERROR', 'Select at least one Agile system.', parent=window)
            return

        ticket_no = ticket_no_var.get().strip()
        if not ticket_no:
            messagebox.showerror('INPUT_ERROR', 'Ticket number is required.', parent=window)
            ticket_entry.focus_set()
            return

        emp_id = emp_id_var.get().strip()
        if not emp_id:
            messagebox.showerror('INPUT_ERROR', 'Employee ID is required.', parent=window)
            emp_entry.focus_set()
            return

        screenshot_path = screenshot_var.get().strip()
        if not screenshot_path:
            messagebox.showerror('INPUT_ERROR', 'Ticket screenshot is required.', parent=window)
            return
        if not os.path.exists(screenshot_path):
            messagebox.showerror('INPUT_ERROR', 'Selected screenshot file could not be found.', parent=window)
            return

        log_event(
            "agile.reset",
            "Preparing Agile password reset email",
            details={"systems": selected_systems, "employee": emp_id},
        )

        try:
            send_agile_reset_email(selected_systems, ticket_no, emp_id, screenshot_path)
        except Exception as exc:
            log_event(
                "agile.reset",
                "Agile password reset email failed",
                level='error',
                details={"error": str(exc), "ticket": ticket_no},
            )
            messagebox.showerror(
                'ERROR',
                f'Failed to prepare Agile password reset email.\n\nDetails: {exc}',
                parent=window,
            )
            return

        log_event(
            "agile.reset",
            "Agile password reset email prepared",
            details={"ticket": ticket_no, "employee": emp_id},
        )
        messagebox.showinfo('SUCCESS', 'Agile password reset email prepared and sent.', parent=window)
        window.destroy()

    ttk.Button(main_frame, text='[EXECUTE] SEND_REQUEST', style='AgileResetButton.TButton', command=submit).pack(fill='x')

    ticket_entry.focus_set()
    parent = window.master
    if parent:
        window.transient(parent)
    window.grab_set()
    window.bind('<Escape>', lambda _e: window.destroy())


def build_telco_section(parent: tk.Widget) -> None:
    section = ttk.LabelFrame(parent, text="📞 Monthly Telco Bill Process", style='MainTech.TLabelframe')
    section.pack(fill='x', pady=(0, 20))
    container = ttk.Frame(section, style='MainTech.TFrame')
    container.pack(fill='x', padx=20, pady=16)
    
    # Warning label about signatures
    warning_frame = tk.Frame(container, bg=WARNING, relief='solid', borderwidth=1)
    warning_frame.pack(fill='x', pady=(0, 15))
    warning_label = tk.Label(
        warning_frame,
        text="⚠ IMPORTANT: Please make sure there are 2 signatures for both Singtel and M1 before proceed with Automation tool",
        font=('Segoe UI', 10, 'bold'),
        bg=WARNING,
        fg='#000000',
        wraplength=500,
        justify='left',
        padx=10,
        pady=8
    )
    warning_label.pack()

    ttk.Button(
        container,
        text="📄 Process Singtel Bills",
        command=launch_singtel_process,
        style='InfoButton.TButton'
    ).pack(fill='x', pady=(0, 10))

    ttk.Button(
        container,
        text="📱 Process M1 Bill",
        command=launch_m1_process,
        style='MainTechButton.TButton'
    ).pack(fill='x')


def launch_singtel_process():
    """Launch Singtel bill processing workflow."""
    # Select 2 PDF files
    pdf1 = filedialog.askopenfilename(
        title="Select First PDF (will be renamed to IGS SIP)",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not pdf1:
        log_event("telco.singtel", "Singtel process cancelled - missing first PDF", level='warning')
        return

    pdf2 = filedialog.askopenfilename(
        title="Select Second PDF (will be renamed to IGS Telco)",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not pdf2:
        log_event("telco.singtel", "Singtel process cancelled - missing second PDF", level='warning')
        return

    # Get paths from config or prompt
    igs32_path = get_path("singtel_igs32_path")
    if not igs32_path:
        igs32_path = filedialog.askdirectory(title="Select Singtel-IGS.32 folder path")
        if not igs32_path:
            messagebox.showerror("INPUT_ERROR", "IGS.32 path is required.")
            return
        set_path("singtel_igs32_path", igs32_path)
    
    cnt35_path = get_path("singtel_cnt35_path")
    if not cnt35_path:
        cnt35_path = filedialog.askdirectory(title="Select Singtel-CNT.35 folder path")
        if not cnt35_path:
            messagebox.showerror("INPUT_ERROR", "CNT.35 path is required.")
            return
        set_path("singtel_cnt35_path", cnt35_path)
    
    # Confirm before processing
    confirm = messagebox.askyesno(
        "CONFIRM_SINGTEL_PROCESS",
        "Process Singtel bills?\n\n"
        f"PDF 1: {os.path.basename(pdf1)}\n"
        f"PDF 2: {os.path.basename(pdf2)}\n\n"
        f"Files will be copied to:\n"
        f"- {igs32_path}\n"
        f"- {cnt35_path}\n\n"
        "Email will be sent after processing."
        )
    if not confirm:
        log_event(
            "telco.singtel",
            "Singtel process cancelled at confirmation",
            level='warning',
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
        # Process bills
        result = process_singtel_bills(pdf1, pdf2, igs32_path, cnt35_path)

        # Send email with attachments from IGS.32
        send_singtel_telco_email(
            result['sip_igs32'],
            result['telco_igs32'],
            result['igs32_path']
        )

        log_event(
            "telco.singtel",
            "Singtel bills processed and email dispatched",
            details={
                "igs32_output": result['igs32_path'],
                "cnt35_output": cnt35_path,
            },
        )

        messagebox.showinfo(
            "SUCCESS",
            "Singtel bills processed successfully!\n\n"
            f"Files saved to:\n"
            f"- IGS.32: {igs32_path}\n"
            f"- CNT.35: {cnt35_path}\n\n"
            "Email sent with attachments."
        )
    except Exception as e:
        log_event(
            "telco.singtel",
            "Singtel bill processing failed",
            level='error',
            details={"error": str(e)},
        )
        messagebox.showerror(
            "ERROR",
            f"Error processing Singtel bills:\n\n{str(e)}"
        )


def launch_m1_process():
    """Launch M1 bill processing workflow."""
    # Select PDF file
    pdf_path = filedialog.askopenfilename(
        title="Select M1 PDF",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not pdf_path:
        log_event("telco.m1", "M1 process cancelled - PDF not selected", level='warning')
        return
    
    # Get paths from config or prompt
    igs32_path = get_path("m1_igs32_path")
    if not igs32_path:
        igs32_path = filedialog.askdirectory(title="Select M1-IGS.32 folder path")
        if not igs32_path:
            messagebox.showerror("INPUT_ERROR", "M1-IGS.32 path is required.")
            log_event("telco.m1", "M1 process cancelled - missing IGS.32 path", level='warning')
            return
        set_path("m1_igs32_path", igs32_path)
    
    cnt35_path = get_path("m1_cnt35_path")
    if not cnt35_path:
        cnt35_path = filedialog.askdirectory(title="Select M1-CNT.35 folder path")
        if not cnt35_path:
            messagebox.showerror("INPUT_ERROR", "M1-CNT.35 path is required.")
            log_event("telco.m1", "M1 process cancelled - missing CNT.35 path", level='warning')
            return
        set_path("m1_cnt35_path", cnt35_path)
    
    # Get Excel paths
    igs32_excel = get_path("m1_igs32_excel")
    if not igs32_excel or not os.path.exists(igs32_excel):
        igs32_excel = filedialog.askopenfilename(
            title="Select IGS-Summarize-M1-Bill Excel (IGS.32)",
            filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        )
        if not igs32_excel:
            messagebox.showerror("INPUT_ERROR", "IGS.32 Excel file is required.")
            log_event("telco.m1", "M1 process cancelled - missing IGS.32 Excel", level='warning')
            return
        set_path("m1_igs32_excel", igs32_excel)
    
    cnt35_excel = get_path("m1_cnt35_excel")
    if not cnt35_excel or not os.path.exists(cnt35_excel):
        cnt35_excel = filedialog.askopenfilename(
            title="Select IGS-Summarize-M1-Bill Excel (CNT.35)",
            filetypes=[("Excel files", "*.xlsx;*.xls"), ("All files", "*.*")]
        )
        if not cnt35_excel:
            messagebox.showerror("INPUT_ERROR", "CNT.35 Excel file is required.")
            log_event("telco.m1", "M1 process cancelled - missing CNT.35 Excel", level='warning')
            return
        set_path("m1_cnt35_excel", cnt35_excel)
    
    # Prompt for monthly amount
    from tkinter import simpledialog
    user_amount = simpledialog.askfloat(
        "M1 Monthly Amount",
        "Enter this month's M1 bill amount (with GST):",
        minvalue=0.0
    )
    if user_amount is None:
        messagebox.showwarning("CANCELLED", "Amount is required.")
        log_event("telco.m1", "M1 process cancelled - amount not provided", level='warning')
        return
    
    # Confirm before processing
    confirm = messagebox.askyesno(
        "CONFIRM_M1_PROCESS",
        f"Process M1 bill?\n\n"
        f"PDF: {os.path.basename(pdf_path)}\n"
        f"Amount (with GST): ${user_amount:.2f}\n\n"
        f"Files will be copied to:\n"
        f"- {igs32_path}\n"
        f"- {cnt35_path}\n\n"
        "Excel files will be updated and email will be sent."
    )
    if not confirm:
        log_event(
            "telco.m1",
            "M1 process cancelled at confirmation",
            level='warning',
            details={"pdf": os.path.basename(pdf_path), "amount": user_amount},
        )
        return

    try:
        log_event(
            "telco.m1",
            "Processing M1 bill",
            details={
                "pdf": os.path.basename(pdf_path),
                "amount": user_amount,
                "igs32_path": igs32_path,
                "cnt35_path": cnt35_path,
            },
        )
        # Process M1 bill (copy PDFs)
        result = process_m1_bill(pdf_path, igs32_path, cnt35_path)

        # Update both Excel files
        excel_results = update_both_m1_excels(igs32_excel, cnt35_excel, user_amount)
        
        # Build summary message
        summary_lines = [f"M1 bill processed successfully!\n"]
        summary_lines.append(f"PDF saved to both paths.\n")
        
        if excel_results['igs32']['success']:
            prev_month = excel_results['igs32']['prev_month']
            prev_amt = excel_results['igs32']['prev_amount']
            summary_lines.append(f"IGS.32 Excel updated:")
            summary_lines.append(f"  Previous: {prev_month} = ${prev_amt:.2f}")
            summary_lines.append(f"  Current: ${user_amount:.2f}")
        else:
            summary_lines.append(f"IGS.32 Excel update failed: {excel_results['igs32']['error']}")
        
        if excel_results['cnt35']['success']:
            summary_lines.append(f"\nCNT.35 Excel updated successfully.")
        else:
            summary_lines.append(f"\nCNT.35 Excel update failed: {excel_results['cnt35']['error']}")
        
        # Show summary
        messagebox.showinfo("PROCESS_SUMMARY", "\n".join(summary_lines))

        # Send email with PDF from IGS.32
        send_m1_telco_email(result['m1_igs32'])

        log_event(
            "telco.m1",
            "M1 bill processed and email dispatched",
            details={
                "amount": user_amount,
                "igs32_pdf": result['m1_igs32'],
                "igs32_excel": igs32_excel,
                "cnt35_excel": cnt35_excel,
            },
        )

        messagebox.showinfo("SUCCESS", "Email sent successfully!")

    except PermissionError:
        log_event(
            "telco.m1",
            "Excel file locked during M1 process",
            level='error',
            details={"igs32_excel": igs32_excel, "cnt35_excel": cnt35_excel},
        )
        messagebox.showerror(
            "FILE_LOCKED",
            "Cannot update Excel file.\n\n"
            "Please close the Excel file and try again."
        )
    except Exception as e:
        log_event(
            "telco.m1",
            "M1 bill processing failed",
            level='error',
            details={"error": str(e)},
        )
        messagebox.showerror(
            "ERROR",
            f"Error processing M1 bill:\n\n{str(e)}"
        )


def show_settings_dialog(root: tk.Tk) -> None:
    dialog = tk.Toplevel(root)
    dialog.title("Settings")
    dialog.geometry("780x600")
    dialog.configure(bg=BASE_BG)

    style = ttk.Style(dialog)
    style.configure('Settings.TFrame', background=BASE_BG)
    style.configure('SettingsPanel.TFrame', background=PANEL_BG)
    style.configure('Settings.TLabelframe', background=PANEL_BG, foreground=ACCENT, borderwidth=1, relief='solid', padding=18)
    style.configure('Settings.TLabelframe.Label', background=PANEL_BG, foreground=ACCENT, font=('Consolas', 11, 'bold'))
    style.configure('Settings.TLabel', background=PANEL_BG, foreground=TEXT_PRIMARY, font=('Consolas', 10))
    style.configure('Settings.TEntry', fieldbackground=INPUT_BG, foreground=TEXT_PRIMARY, insertcolor=ACCENT, font=('Consolas', 10))
    style.configure('SettingsButton.TButton', background=POSITIVE, foreground='#ffffff', padding=(12, 8), font=('Consolas', 11, 'bold'))
    style.map(
        'SettingsButton.TButton',
        background=[('active', '#68B491'), ('pressed', '#5AA884')],
    )

    active_profile = get_active_profile_name()
    profile_var = tk.StringVar(value=active_profile)

    profile_names = list_profiles()
    if active_profile not in profile_names:
        profile_names.append(active_profile)

    path_keys = set()
    for name in profile_names:
        path_keys.update(list_paths(name).keys())
    if not path_keys:
        path_keys.update(list_paths(active_profile).keys())
    path_keys = sorted(path_keys)

    email_field_map: Dict[str, set[str]] = {}
    for name in profile_names:
        sections = list_email_sections(name)
        for section, data in sections.items():
            if not isinstance(data, dict):
                continue
            email_field_map.setdefault(section, set()).update(data.keys())
    if not email_field_map:
        sections = list_email_sections(active_profile)
        for section, data in sections.items():
            if isinstance(data, dict):
                email_field_map.setdefault(section, set()).update(data.keys())

    notebook_container = ttk.Frame(dialog, style='Settings.TFrame')
    notebook_container.pack(fill='both', expand=True, padx=15, pady=15)

    notebook_canvas = tk.Canvas(notebook_container, bg=BASE_BG, highlightthickness=0)
    notebook_scrollbar = ttk.Scrollbar(notebook_container, orient='vertical', command=notebook_canvas.yview)
    notebook_canvas.pack(side='left', fill='both', expand=True)
    notebook_scrollbar.pack(side='right', fill='y')

    inner_frame = ttk.Frame(notebook_canvas, style='Settings.TFrame')
    inner_frame.bind('<Configure>', lambda e: notebook_canvas.configure(scrollregion=notebook_canvas.bbox('all')))
    notebook_canvas.create_window((0, 0), window=inner_frame, anchor='nw')
    notebook_canvas.configure(yscrollcommand=notebook_scrollbar.set)

    notebook = ttk.Notebook(inner_frame)
    notebook.pack(fill='both', expand=True)

    profiles_frame = ttk.Frame(notebook, style='Settings.TFrame')
    paths_frame = ttk.Frame(notebook, style='Settings.TFrame')
    email_frame = ttk.Frame(notebook, style='Settings.TFrame')
    signature_frame = ttk.Frame(notebook, style='Settings.TFrame')

    notebook.add(profiles_frame, text='Profiles & Backups')
    notebook.add(paths_frame, text='Paths')
    notebook.add(email_frame, text='Email Recipients')
    notebook.add(signature_frame, text='Signature')

    path_entries: Dict[str, ttk.Entry] = {}

    def browse_for_path(key: str) -> None:
        current = path_entries[key].get().strip()
        initialdir = current if current and os.path.exists(os.path.dirname(current) if os.path.isfile(current) else current) else os.getcwd()
        if key.endswith('_folder') or key.endswith('_dir'):
            selected = filedialog.askdirectory(parent=dialog, title=f'Select folder for {key}', initialdir=initialdir)
        else:
            selected = filedialog.askopenfilename(parent=dialog, title=f'Select file for {key}', initialdir=initialdir)
        if selected:
            path_entries[key].delete(0, 'end')
            path_entries[key].insert(0, selected)

    for idx, key in enumerate(path_keys):
        row = ttk.Frame(paths_frame, style='Settings.TFrame')
        row.grid(row=idx, column=0, sticky='ew', pady=8, padx=10)
        ttk.Label(row, text=key, style='Settings.TLabel', width=26, anchor='w').pack(side='left')
        entry = ttk.Entry(row, style='Settings.TEntry')
        entry.pack(side='left', fill='x', expand=True, padx=(10, 10))
        ttk.Button(row, text='Browse', command=lambda k=key: browse_for_path(k)).pack(side='right')
        path_entries[key] = entry

    email_entries: Dict[tuple[str, str], ttk.Entry] = {}
    for section in sorted(email_field_map.keys()):
        section_frame = ttk.LabelFrame(email_frame, text=section.upper(), style='Settings.TLabelframe')
        section_frame.pack(fill='x', padx=10, pady=10)
        fields = sorted(email_field_map[section] or {'to', 'cc'})
        for field in fields:
            row = ttk.Frame(section_frame, style='Settings.TFrame')
            row.pack(fill='x', pady=6)
            ttk.Label(row, text=field.upper(), style='Settings.TLabel', width=10, anchor='w').pack(side='left')
            entry = ttk.Entry(row, style='Settings.TEntry')
            entry.pack(side='left', fill='x', expand=True, padx=(10, 0))
            email_entries[(section, field)] = entry

    signature_label = ttk.Label(signature_frame, text='HTML footer used for all emails.', style='Settings.TLabel')
    signature_label.pack(anchor='w', padx=12, pady=(12, 6))
    signature_text = tk.Text(signature_frame, height=10, wrap='word', font=('Consolas', 10), bg=INPUT_BG, fg=TEXT_PRIMARY, insertbackground=ACCENT, borderwidth=1, relief='solid')
    signature_text.pack(fill='both', expand=True, padx=12, pady=(0, 12))

    backups_label = ttk.Label(profiles_frame, text='Environment profile', style='Settings.TLabel')
    backups_label.pack(anchor='w', padx=12, pady=(12, 6))

    profile_combo = ttk.Combobox(profiles_frame, textvariable=profile_var, state='readonly')
    profile_combo.pack(fill='x', padx=12, pady=(0, 12))

    new_profile_var = tk.StringVar()
    new_profile_row = ttk.Frame(profiles_frame, style='Settings.TFrame')
    new_profile_row.pack(fill='x', padx=12, pady=(0, 12))
    ttk.Entry(new_profile_row, textvariable=new_profile_var, style='Settings.TEntry').pack(side='left', fill='x', expand=True)
    ttk.Button(new_profile_row, text='Create Profile', command=lambda: create_new_profile()).pack(side='left', padx=(10, 0))

    ttk.Button(profiles_frame, text='Delete Selected Profile', command=lambda: delete_selected_profile(), style='SettingsButton.TButton').pack(anchor='e', padx=12, pady=(0, 12))

    ttk.Label(profiles_frame, text='Recent configuration backups', style='Settings.TLabel').pack(anchor='w', padx=12, pady=(12, 6))
    backups_list = tk.Listbox(
        profiles_frame,
        height=6,
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        selectbackground=ACCENT,
        borderwidth=0,
        highlightthickness=0,
    )
    backups_list.pack(fill='both', expand=True, padx=12, pady=(0, 12))

    status_var = tk.StringVar()
    status_label = ttk.Label(dialog, textvariable=status_var, foreground=ACCENT, background=BASE_BG, font=('Consolas', 10))
    status_label.pack(fill='x', padx=15, pady=(0, 5))

    def populate_fields(profile_name: str) -> None:
        current_paths = list_paths(profile_name)
        for key, entry in path_entries.items():
            entry.delete(0, 'end')
            entry.insert(0, current_paths.get(key, ''))

        sections = list_email_sections(profile_name)
        for (section, field), entry in email_entries.items():
            value = ''
            section_data = sections.get(section)
            if isinstance(section_data, dict):
                value = section_data.get(field, '')
            entry.delete(0, 'end')
            entry.insert(0, value)

        signature_text.delete('1.0', 'end')
        signature_text.insert('1.0', get_signature_text(profile_name))

    def refresh_backups() -> None:
        backups_list.delete(0, 'end')
        for entry in list_config_backups(limit=12):
            timestamp = entry.get('timestamp', 'unknown')
            profile = entry.get('active_profile', 'default')
            action = entry.get('action', 'update')
            backup_file = entry.get('backup_file', '')
            backups_list.insert('end', f"{timestamp} | {profile} | {action} -> {backup_file}")

    def refresh_profiles(select: str | None = None) -> None:
        names = list_profiles()
        profile_combo['values'] = names
        if select:
            profile_var.set(select)
        elif profile_var.get() not in names and names:
            profile_var.set(names[0])
        populate_fields(profile_var.get())
        refresh_backups()
        if hasattr(root, 'active_profile_var'):
            root.active_profile_var.set(profile_var.get())

    def on_profile_selected(event=None) -> None:
        selected = profile_var.get()
        current_active = get_active_profile_name()
        if selected != current_active:
            try:
                set_active_profile(selected)
            except ValueError as exc:
                status_var.set(str(exc))
                profile_var.set(current_active)
                return
            log_event('config.profile', 'Switched active configuration profile', details={'profile': selected})
        populate_fields(selected)
        refresh_backups()
        status_var.set(f"Active profile set to '{selected}'.")
        dialog.after(2500, lambda: status_var.set(''))
        if hasattr(root, 'active_profile_var'):
            root.active_profile_var.set(selected)

    def create_new_profile() -> None:
        name = new_profile_var.get().strip()
        if not name:
            status_var.set('Enter a profile name before creating.')
            return
        try:
            create_profile(name, source_profile=profile_var.get())
        except ValueError as exc:
            status_var.set(str(exc))
            return
        new_profile_var.set('')
        log_event('config.profile', 'Created configuration profile', details={'profile': name})
        status_var.set(f"Profile '{name}' created.")
        refresh_profiles(select=name)
        dialog.after(2500, lambda: status_var.set(''))

    def delete_selected_profile() -> None:
        target = profile_var.get()
        if target == 'default':
            status_var.set('Default profile cannot be deleted.')
            return
        if not messagebox.askyesno('Delete Profile', f"Delete profile '{target}'? This cannot be undone.", parent=dialog):
            return
        try:
            delete_profile(target)
        except ValueError as exc:
            status_var.set(str(exc))
            return
        log_event('config.profile', 'Deleted configuration profile', details={'profile': target})
        status_var.set(f"Profile '{target}' deleted.")
        refresh_profiles(select='default')
        dialog.after(2500, lambda: status_var.set(''))

    def save_settings() -> None:
        selected_profile = profile_var.get()
        paths_payload = {key: entry.get().strip() for key, entry in path_entries.items()}
        email_payload: Dict[str, Dict[str, str]] = {}
        for (section, field), entry in email_entries.items():
            email_payload.setdefault(section, {})[field] = entry.get().strip()
        signature_value = signature_text.get('1.0', 'end').strip()

        try:
            update_profile_settings(
                selected_profile,
                paths=paths_payload,
                email_settings=email_payload,
                signature=signature_value,
            )
        except Exception as exc:
            status_var.set(f'Failed to save settings: {exc}')
            log_event('config', 'Failed to save configuration', level='error', details={'error': str(exc)})
            return

        log_event('config', 'Configuration updated', details={'profile': selected_profile})
        status_var.set(f"Settings saved for profile '{selected_profile}'.")
        refresh_backups()
        dialog.after(2500, lambda: status_var.set(''))

    profile_combo.bind('<<ComboboxSelected>>', on_profile_selected)

    refresh_profiles(select=profile_var.get())

    buttons = ttk.Frame(dialog, style='Settings.TFrame')
    buttons.pack(fill='x', padx=15, pady=(0, 15))
    ttk.Button(buttons, text='Save', style='SettingsButton.TButton', command=save_settings).pack(side='right')
    ttk.Button(buttons, text='Close', command=dialog.destroy).pack(side='right', padx=(0, 10))

    if root and root.winfo_exists():
        dialog.transient(root)
    dialog.grab_set()
    dialog.bind('<Escape>', lambda _e: dialog.destroy())


