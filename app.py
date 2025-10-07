"""Application entry point for IT admin tool."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import datetime

from config_manager import load_config
from ui import (build_user_management_section, build_sap_section,
                build_agile_section, build_telco_section, show_settings_dialog)


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
                        '---`"                       
"""


def create_main_gui():
    root = tk.Tk()
    root.title("IT ! IT - Modern Admin Toolkit")
    
    # Balanced Dark Theme - Professional & Easy to Read
    base_bg = '#1a1d29'  # Soft dark blue-gray (not too dark)
    panel_bg = '#242837'  # Slightly lighter panels for depth
    accent = '#60a5fa'  # Bright blue (high contrast)
    secondary_accent = '#34d399'  # Bright mint green
    positive = '#34d399'  # Bright green
    info_bg = '#3b82f6'  # Vibrant blue
    warning_bg = '#fbbf24'  # Bright yellow
    danger_bg = '#f87171'  # Bright coral red
    text_primary = '#f1f5f9'  # Almost white text for readability
    text_muted = '#94a3b8'  # Light gray for secondary text
    border_color = '#334155'  # Subtle borders
    shadow_color = '#0f1419'  # Deep shadow
    
    root.configure(bg=base_bg)

    style = ttk.Style()
    style.theme_use('clam')
    
    # Main frame with light background
    style.configure('MainTech.TFrame', background=base_bg, relief='flat')
    
    # Card-style panels with subtle shadows
    style.configure('MainTech.TLabelframe', 
                   background=panel_bg, 
                   foreground=accent, 
                   borderwidth=0, 
                   relief='flat', 
                   padding=24)
    style.configure('MainTech.TLabelframe.Label', 
                   background=panel_bg, 
                   foreground=accent, 
                   font=('Segoe UI', 11, 'bold'))
    
    # Modern rounded buttons with gradients
    style.configure('MainTechButton.TButton', 
                   background=positive, 
                   foreground='#ffffff', 
                   borderwidth=0, 
                   padding=(20, 14), 
                   font=('Segoe UI', 10, 'bold'),
                   relief='flat')
    style.map('MainTechButton.TButton', 
             background=[('active', '#059669'), ('pressed', '#047857')],
             relief=[('pressed', 'flat')])
    
    style.configure('InfoButton.TButton', 
                   background=info_bg, 
                   foreground='#ffffff', 
                   borderwidth=0, 
                   padding=(20, 14), 
                   font=('Segoe UI', 10, 'bold'),
                   relief='flat')
    style.map('InfoButton.TButton', 
             background=[('active', '#0284c7'), ('pressed', '#0369a1')])
    
    style.configure('DangerButton.TButton', 
                   background=danger_bg, 
                   foreground='#ffffff', 
                   borderwidth=0, 
                   padding=(20, 14), 
                   font=('Segoe UI', 10, 'bold'),
                   relief='flat')
    style.map('DangerButton.TButton', 
             background=[('active', '#dc2626'), ('pressed', '#b91c1c')])

    screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
    window_width = min(max(800, int(screen_width * 0.7)), 1200)
    window_height = min(max(600, int(screen_height * 0.8)), 900)
    root.geometry(f"{window_width}x{window_height}")
    root.minsize(700, 500)

    main_canvas = tk.Canvas(root, bg=base_bg, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    scrollable_frame = ttk.Frame(main_canvas, style='MainTech.TFrame')
    
    def update_scroll_region(event=None):
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        # Center the content horizontally
        canvas_width = main_canvas.winfo_width()
        frame_width = scrollable_frame.winfo_reqwidth()
        x_position = max(0, (canvas_width - frame_width) // 2)
        main_canvas.coords(main_canvas.find_withtag("content_window")[0], x_position, 0)
    
    scrollable_frame.bind("<Configure>", update_scroll_region)
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="n", tags="content_window")
    main_canvas.configure(yscrollcommand=scrollbar.set)
    main_canvas.pack(side="left", fill="both", expand=True)

    def on_canvas_configure(event):
        update_scroll_region()
        if main_canvas.bbox("all") and main_canvas.bbox("all")[3] > main_canvas.winfo_height():
            scrollbar.pack(side="right", fill="y")
        else:
            scrollbar.pack_forget()

    main_canvas.bind('<Configure>', on_canvas_configure)

    def _on_mousewheel(event):
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    main_canvas.bind('<Enter>', lambda _: main_canvas.bind_all("<MouseWheel>", _on_mousewheel))
    main_canvas.bind('<Leave>', lambda _: main_canvas.unbind_all("<MouseWheel>"))

    header = ttk.Frame(scrollable_frame, style='MainTech.TFrame')
    header.pack(fill='x', pady=(20, 40))
    
    # Modern header with gradient feel
    tk.Label(header, text=ASCII_BANNER, font=('Consolas', 5), bg=base_bg, fg='#ff6b6b', justify='center').pack()
    tk.Label(header, text="// INGRASYS IT ADMIN AUTOMATION TOOLKIT", 
            font=('Segoe UI', 14, 'bold'), bg=base_bg, fg=text_primary).pack(pady=(10, 2))
    tk.Label(header, text="// COLLAB WITH CODEX&CLAUDE", 
            font=('Segoe UI', 10), bg=base_bg, fg=text_muted).pack()
    
    # Status badge with modern styling
    status_frame = tk.Frame(header, bg=base_bg)
    status_frame.pack(pady=(15, 0))
    status_label = tk.Label(status_frame, 
                           text=f"● Online • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                           font=('Segoe UI', 9), 
                           bg='#1e3a2e',  # Dark green background
                           fg='#34d399',  # Bright green text
                           padx=16, 
                           pady=6,
                           relief='flat')
    status_label.pack()

    # Sections frame - content will auto-center via canvas positioning
    sections_frame = ttk.Frame(scrollable_frame, style='MainTech.TFrame')
    sections_frame.pack(pady=(0, 20))

    build_user_management_section(sections_frame)
    build_sap_section(sections_frame)
    build_agile_section(sections_frame)
    build_telco_section(sections_frame)

    footer = tk.Label(scrollable_frame, 
                     text="Press ESC to exit • Use settings to customize configuration", 
                     font=('Segoe UI', 9), 
                     bg=base_bg, 
                     fg=text_muted)
    footer.pack(fill='x', side='bottom', pady=20)

    def on_escape(event):
        root.quit()

    root.bind('<Escape>', on_escape)

    def open_settings():
        show_settings_dialog(root)

    settings_button = ttk.Button(header, text="⚙ Settings", style='InfoButton.TButton', command=open_settings)
    settings_button.pack(pady=15)

    def initialize_window():
        root.update_idletasks()
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        # Center window on screen
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        update_scroll_region()
    
    # Handle window resize to keep content centered
    def on_window_resize(event):
        if event.widget == root:
            root.after(10, update_scroll_region)
    
    root.bind('<Configure>', on_window_resize)
    root.after(100, initialize_window)
    root.mainloop()


if __name__ == "__main__":
    create_main_gui()

