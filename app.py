"""Application entry point for IT admin tool."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import ttk

from activity_log import describe_event, get_recent_events, log_event, register_listener
from config_manager import get_active_profile_name
from ui import (
    build_agile_section,
    build_sap_section,
    build_telco_section,
    build_user_management_section,
    show_settings_dialog,
)


ASCII_BANNER = """
                ,----,   ,---,                 ,----,
              ,/   .`|,`--.' |               ,/   .`|
   ,---,    ,`   .'  :|   :  :    ,---,    ,`   .'  :
,`--.' |  ;    ;     /'   '  ; ,`--.' |  ;    ;     /
|   :  :.'___,/    ,' |   |  | |   :  :.'___,/    ,'
:   |  '|    :     |  '   :  ; :   |  '|    :     |
|   :  |;    |.';  ;  |   |  ' |   :  |;    |.';  ;
'   '  ;`----'  |  |  '   :  | '   '  ;`----'  |  |
|   |  |    '   :  ;  ;   |  ; |   |  |    '   :  ;
'   :  ;    |   |  '  `---'. | '   :  ;    |   |  '
|   |  '    '   :  |   `--..`; |   |  '    '   :  |
'   :  |    ;   |.'   .--,_    '   :  |    ;   |.'
;   |.'     '---'     |    |`. ;   |.'     '---'
'---'                 `-- -`, ;'---'
                        '---`
"""


def create_main_gui() -> None:
    root = tk.Tk()
    root.title("IT ! IT - Modern Admin Toolkit")

    base_bg = '#1a1d29'
    panel_bg = '#242837'
    accent = '#60a5fa'
    positive = '#34d399'
    info_bg = '#3b82f6'
    danger_bg = '#f87171'
    text_primary = '#f1f5f9'
    text_muted = '#94a3b8'

    root.configure(bg=base_bg)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('MainTech.TFrame', background=base_bg, relief='flat')
    style.configure('MainTech.TLabelframe', background=panel_bg, foreground=accent, borderwidth=0, relief='flat', padding=24)
    style.configure('MainTech.TLabelframe.Label', background=panel_bg, foreground=accent, font=('Segoe UI', 11, 'bold'))
    style.configure('MainTechButton.TButton', background=positive, foreground='#ffffff', borderwidth=0, padding=(20, 14), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map('MainTechButton.TButton', background=[('active', '#059669'), ('pressed', '#047857')], relief=[('pressed', 'flat')])
    style.configure('InfoButton.TButton', background=info_bg, foreground='#ffffff', borderwidth=0, padding=(20, 14), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map('InfoButton.TButton', background=[('active', '#0284c7'), ('pressed', '#0369a1')])
    style.configure('DangerButton.TButton', background=danger_bg, foreground='#ffffff', borderwidth=0, padding=(20, 14), font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map('DangerButton.TButton', background=[('active', '#dc2626'), ('pressed', '#b91c1c')])
    style.configure('MainTech.TNotebook', background=base_bg, borderwidth=0)
    style.configure('MainTech.TNotebook.Tab', background=panel_bg, foreground=text_primary, padding=(18, 10), font=('Segoe UI', 10, 'bold'))
    style.map('MainTech.TNotebook.Tab', background=[('selected', accent)], foreground=[('selected', '#0f172a')])

    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    window_width = min(max(800, int(screen_width * 0.7)), 1200)
    window_height = min(max(600, int(screen_height * 0.8)), 900)
    root.geometry(f"{window_width}x{window_height}")
    root.minsize(760, 520)

    active_profile_var = tk.StringVar(value=get_active_profile_name())
    root.active_profile_var = active_profile_var
    environment_display_var = tk.StringVar()

    def update_environment_display(*_args: object) -> None:
        environment_display_var.set(f"Environment: {active_profile_var.get()}")

    active_profile_var.trace_add('write', update_environment_display)
    update_environment_display()

    status_message_var = tk.StringVar(value="Ready")

    content_container = tk.Frame(root, bg=base_bg)
    content_container.pack(fill='both', expand=True)

    main_canvas = tk.Canvas(content_container, bg=base_bg, highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_container, orient='vertical', command=main_canvas.yview)
    scrollable_frame = ttk.Frame(main_canvas, style='MainTech.TFrame')

    def update_scroll_region(event: object | None = None) -> None:
        main_canvas.configure(scrollregion=main_canvas.bbox('all'))
        window_items = main_canvas.find_withtag('content_window')
        if window_items:
            canvas_width = main_canvas.winfo_width()
            frame_width = scrollable_frame.winfo_reqwidth()
            x_pos = max(0, (canvas_width - frame_width) // 2)
            main_canvas.coords(window_items[0], x_pos, 0)

    scrollable_frame.bind('<Configure>', update_scroll_region)
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor='n', tags='content_window')
    main_canvas.configure(yscrollcommand=scrollbar.set)
    main_canvas.pack(side='left', fill='both', expand=True)

    def on_canvas_configure(event: object) -> None:
        update_scroll_region()
        if main_canvas.bbox('all') and main_canvas.bbox('all')[3] > main_canvas.winfo_height():
            scrollbar.pack(side='right', fill='y')
        else:
            scrollbar.pack_forget()

    main_canvas.bind('<Configure>', on_canvas_configure)

    def _on_mousewheel(event: tk.Event) -> None:
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    main_canvas.bind('<Enter>', lambda _: main_canvas.bind_all('<MouseWheel>', _on_mousewheel))
    main_canvas.bind('<Leave>', lambda _: main_canvas.unbind_all('<MouseWheel>'))

    header = ttk.Frame(scrollable_frame, style='MainTech.TFrame')
    header.pack(fill='x', pady=(20, 40))
    tk.Label(header, text=ASCII_BANNER, font=('Consolas', 5), bg=base_bg, fg='#ff6b6b', justify='center').pack()
    tk.Label(header, text='// INGRASYS IT ADMIN AUTOMATION TOOLKIT', font=('Segoe UI', 14, 'bold'), bg=base_bg, fg=text_primary).pack(pady=(10, 2))
    tk.Label(header, text='// COLLAB WITH CODEX&CLAUDE', font=('Segoe UI', 10), bg=base_bg, fg=text_muted).pack()

    status_frame = tk.Frame(header, bg=base_bg)
    status_frame.pack(pady=(15, 0))
    status_label = tk.Label(status_frame, font=('Segoe UI', 9), bg='#1e3a2e', fg='#34d399', padx=16, pady=6, relief='flat')
    status_label.pack()

    def refresh_online_badge() -> None:
        status_label.config(text=f"● {active_profile_var.get()} • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def schedule_badge_refresh() -> None:
        refresh_online_badge()
        root.after(60000, schedule_badge_refresh)

    schedule_badge_refresh()
    active_profile_var.trace_add('write', lambda *_: refresh_online_badge())

    sections_frame = ttk.Frame(scrollable_frame, style='MainTech.TFrame')
    sections_frame.pack(pady=(0, 20), fill='both', expand=True)

    notebook = ttk.Notebook(sections_frame, style='MainTech.TNotebook')
    notebook.pack(fill='both', expand=True, padx=20, pady=10)

    def build_tab_frame() -> tuple[ttk.Frame, ttk.Frame]:
        tab = ttk.Frame(notebook, style='MainTech.TFrame')
        inner = ttk.Frame(tab, style='MainTech.TFrame')
        inner.pack(fill='both', expand=True, padx=25, pady=25)
        return tab, inner

    user_tab, user_inner = build_tab_frame()
    sap_tab, sap_inner = build_tab_frame()
    agile_tab, agile_inner = build_tab_frame()
    telco_tab, telco_inner = build_tab_frame()
    activity_tab, activity_inner = build_tab_frame()

    notebook.add(user_tab, text='User Ops')
    notebook.add(sap_tab, text='SAP')
    notebook.add(agile_tab, text='Agile')
    notebook.add(telco_tab, text='Telecom')
    notebook.add(activity_tab, text='Operations Center')

    build_user_management_section(user_inner)
    build_sap_section(sap_inner)
    build_agile_section(agile_inner)
    build_telco_section(telco_inner)

    class ActivityLogPanel:
        def __init__(self, parent: ttk.Frame) -> None:
            self.container = ttk.Frame(parent, style='MainTech.TFrame')
            self.container.pack(fill='both', expand=True)

            header_frame = ttk.Frame(self.container, style='MainTech.TFrame')
            header_frame.pack(fill='x', pady=(0, 12))
            tk.Label(header_frame, text='📜 Recent Activity Log', font=('Segoe UI', 14, 'bold'), bg=base_bg, fg=text_primary).pack(side='left')
            ttk.Button(header_frame, text='Refresh', style='InfoButton.TButton', command=self.refresh).pack(side='right')

            body = tk.Frame(self.container, bg=panel_bg, highlightthickness=0)
            body.pack(fill='both', expand=True)
            self.text = tk.Text(body, bg=panel_bg, fg=text_primary, insertbackground=accent, font=('Consolas', 10), wrap='word', borderwidth=0, relief='flat', state='disabled')
            self.text.pack(side='left', fill='both', expand=True)
            scrollbar_inner = ttk.Scrollbar(body, orient='vertical', command=self.text.yview)
            scrollbar_inner.pack(side='right', fill='y')
            self.text.configure(yscrollcommand=scrollbar_inner.set)
            self.refresh()

        def refresh(self) -> None:
            events = get_recent_events(limit=120)
            lines = [describe_event(entry) for entry in events]
            self.text.configure(state='normal')
            self.text.delete('1.0', 'end')
            for line in lines:
                self.text.insert('end', line + '\n')
            self.text.configure(state='disabled')
            self.text.see('end')

        def append(self, entry: dict) -> None:
            root.after(0, lambda: self._append_entry(entry))

        def _append_entry(self, entry: dict) -> None:
            self.text.configure(state='normal')
            self.text.insert('end', describe_event(entry) + '\n')
            self.text.configure(state='disabled')
            self.text.see('end')

    activity_panel = ActivityLogPanel(activity_inner)

    def on_escape(event: tk.Event) -> None:
        root.quit()

    root.bind('<Escape>', on_escape)

    def open_settings() -> None:
        show_settings_dialog(root)

    settings_button = ttk.Button(header, text='⚙ Settings', style='InfoButton.TButton', command=open_settings)
    settings_button.pack(pady=15)

    def initialize_window() -> None:
        root.update_idletasks()
        main_canvas.configure(scrollregion=main_canvas.bbox('all'))
        x_pos = (screen_width // 2) - (window_width // 2)
        y_pos = (screen_height // 2) - (window_height // 2)
        root.geometry(f'{window_width}x{window_height}+{x_pos}+{y_pos}')
        update_scroll_region()

    def on_window_resize(event: tk.Event) -> None:
        if event.widget == root:
            root.after(10, update_scroll_region)

    root.bind('<Configure>', on_window_resize)

    def on_log_entry(entry: dict) -> None:
        status_message_var.set(describe_event(entry))
        activity_panel.append(entry)

    register_listener(on_log_entry)
    log_event('ui', 'Operator console launched', details={'profile': active_profile_var.get()})

    status_bar = tk.Frame(root, bg=panel_bg)
    status_bar.pack(fill='x', side='bottom')
    tk.Label(status_bar, textvariable=environment_display_var, font=('Segoe UI', 10, 'bold'), bg=panel_bg, fg=accent).pack(side='left', padx=16, pady=8)
    tk.Label(status_bar, textvariable=status_message_var, font=('Segoe UI', 9), bg=panel_bg, fg=text_primary, anchor='w').pack(side='left', padx=12)
    tk.Label(status_bar, text='Press ESC to exit • Use ⚙ Settings to manage configuration', font=('Segoe UI', 9), bg=panel_bg, fg=text_muted).pack(side='right', padx=16)

    root.after(100, initialize_window)
    root.mainloop()


if __name__ == "__main__":
    create_main_gui()
