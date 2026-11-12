import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import threading
import subprocess
import os
import sys
import time
import socket
import ctypes
import re
import webbrowser
import urllib.request
from datetime import datetime
from queue import Queue

# DEMN! By Mr.Rm19 - github.com/Rm19x
try:
    import yt_dlp
    import psutil
    import keyboard
    from PIL import ImageGrab
except ImportError as e:
    print(f"[ERROR] Library belum lengkap: {e}")
    print("Jalankan terminal/CMD: pip install yt-dlp psutil keyboard pillow requests")
    sys.exit(1)

# ==============================================================================
# DEMN! By Mr.Rm19 - github.com/Rm19x
# ==============================================================================
APP_TITLE = "D3D Menu DeemN by Mr.Rm19"
GITHUB_URL = "https://github.com/Rm19x"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "D3D_Downloads")
SCREENSHOT_DIR = os.path.join(os.getcwd(), "D3D_Screenshots")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

THEMES = {
    "Matrix Green": {"bg": "#080C08", "panel": "#0F170F", "fg": "#00FF41", "accent": "#008F11", "text": "#E0FFE0"},
    "Cyberpunk Blue": {"bg": "#060B14", "panel": "#0D1726", "fg": "#00F0FF", "accent": "#0077FF", "text": "#E0F7FF"},
    "Blood Red": {"bg": "#120505", "panel": "#1F0909", "fg": "#FF2A2A", "accent": "#990000", "text": "#FFE0E0"},
    "Vaporwave Purple": {"bg": "#100617", "panel": "#1C0B29", "fg": "#D900FF", "accent": "#7700B3", "text": "#F5E0FF"},
    "Gold Edition": {"bg": "#120E04", "panel": "#1F1807", "fg": "#FFD700", "accent": "#B8860B", "text": "#FFF8DC"},
}

URL_PATTERN = re.compile(
    r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com|instagram\.com|twitter\.com|x\.com)/[^\s]+)'
)


class D3DMenuExplorer:
    def __init__(self, root):
        self.root = root
        self.current_theme_name = "Matrix Green"
        self.theme = THEMES[self.current_theme_name]
        self.hotkey = "insert"
        self.is_visible = True
        self.alpha_val = 0.92
        self.matrix_running = True

        self.download_queue = Queue()
        self.sniffer_enabled = tk.BooleanVar(value=True)
        self.download_thumb = tk.BooleanVar(value=True)

        self.last_clipboard = ""

        self.root.title(APP_TITLE)
        self.root.geometry("480x680+30+40")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.alpha_val)
        self.root.configure(bg=self.theme["bg"])

        self._drag_x = 0
        self._drag_y = 0

        self.last_net = psutil.net_io_counters()
        self.last_net_time = time.time()

        self._build_ui()
        self._bind_hotkey(self.hotkey)
        self._start_background_threads()

    def _build_ui(self):
        self.header_canvas = tk.Canvas(
            self.root, height=62, bg=self.theme["bg"], highlightthickness=1,
            highlightbackground=self.theme["fg"]
        )
        self.header_canvas.pack(fill="x", padx=4, pady=(4, 2))
        self.header_canvas.bind("<Button-1>", self._start_drag)
        self.header_canvas.bind("<B1-Motion>", self._do_drag)

        self.matrix_cols = 48
        self.matrix_drops = [0 for _ in range(self.matrix_cols)]
        self._animate_matrix()

        self.title_label = tk.Label(
            self.header_canvas,
            text=" D3D MENU NETWORK By Mr.Rm19",
            font=("Consolas", 11, "bold"),
            fg=self.theme["fg"],
            bg=self.theme["bg"]
        )
        self.title_label.place(x=10, y=8)
        self.title_label.bind("<Button-1>", self._start_drag)
        self.title_label.bind("<B1-Motion>", self._do_drag)

        self.sub_label = tk.Label(
            self.header_canvas,
            text=f"Hotkey: [{self.hotkey.upper()}] Hide/Show | github.com/Rm19x",
            font=("Consolas", 8),
            fg=self.theme["text"],
            bg=self.theme["bg"]
        )
        self.sub_label.place(x=10, y=34)

        self.btn_hide = tk.Button(
            self.header_canvas, text="_", command=self.toggle_visibility,
            bg=self.theme["panel"], fg=self.theme["fg"], bd=0, font=("Consolas", 9, "bold"), width=3
        )
        self.btn_hide.place(x=415, y=8)

        self.btn_exit = tk.Button(
            self.header_canvas, text="X", command=self.clean_exit,
            bg="#440000", fg="#FF5555", bd=0, font=("Consolas", 9, "bold"), width=3
        )
        self.btn_exit.place(x=445, y=8)

        self.stats_frame = tk.Frame(self.root, bg=self.theme["panel"], bd=1, relief="solid")
        self.stats_frame.pack(fill="x", padx=4, pady=2)

        self.lbl_sys_stats = tk.Label(
            self.stats_frame,
            text="CPU: 0% | RAM: 0% | DL: 0 KB/s | UL: 0 KB/s",
            font=("Consolas", 8, "bold"),
            fg=self.theme["fg"],
            bg=self.theme["panel"]
        )
        self.lbl_sys_stats.pack(pady=3)

        self.tab_bar = tk.Frame(self.root, bg=self.theme["bg"])
        self.tab_bar.pack(fill="x", padx=4, pady=3)

        self.tabs = {}
        self.tab_buttons = {}
        tab_names = ["[DOWNLOADER]", "[WIN CLEANER]", "[SYS & NET]", "[D3D CONFIG]"]

        for name in tab_names:
            btn = tk.Button(
                self.tab_bar, text=name, font=("Consolas", 8, "bold"),
                bg=self.theme["panel"], fg=self.theme["text"],
                activebackground=self.theme["fg"], activeforeground="#000000",
                bd=1, relief="flat", padx=4, pady=4,
                command=lambda n=name: self.switch_tab(n)
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)
            self.tab_buttons[name] = btn

        self.content_area = tk.Frame(self.root, bg=self.theme["bg"])
        self.content_area.pack(fill="both", expand=True, padx=4, pady=2)

        self._build_tab_downloader()
        self._build_tab_win_cleaner()  # DEMN! By Mr.Rm19 - github.com/Rm19x
        self._build_tab_sys_net()
        self._build_tab_config()

        self.status_bar = tk.Label(
            self.root, text="[READY] System initialized by Mr.Rm19...",
            font=("Consolas", 8), fg=self.theme["fg"], bg=self.theme["panel"],
            anchor="w", padx=6, pady=3
        )
        self.status_bar.pack(fill="x", padx=4, pady=(2, 4))

        self.switch_tab("[DOWNLOADER]")

    def _animate_matrix(self):
        if not self.matrix_running:
            return
        self.header_canvas.delete("matrix")
        chars = "01XYZRM19#$%"
        for i in range(self.matrix_cols):
            char = chars[(self.matrix_drops[i] + i) % len(chars)]
            x = i * 10 + 5
            y = self.matrix_drops[i] * 10
            self.header_canvas.create_text(
                x, y, text=char, fill=self.theme["accent"],
                font=("Consolas", 8), tags="matrix"
            )
            if y > 65 and (i % 3 == 0):
                self.matrix_drops[i] = 0
            else:
                self.matrix_drops[i] += 1
        self.root.after(120, self._animate_matrix)

    def _build_tab_downloader(self):
        frame = tk.Frame(self.content_area, bg=self.theme["panel"], bd=1, relief="solid")
        self.tabs["[DOWNLOADER]"] = frame

        top_opt = tk.Frame(frame, bg=self.theme["panel"])
        top_opt.pack(fill="x", padx=8, pady=(6, 2))

        tk.Checkbutton(
            top_opt, text="[ON] Auto-Sniff Clipboard URL", variable=self.sniffer_enabled,
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"],
            selectcolor="#000000", activebackground=self.theme["panel"]
        ).pack(side="left")

        tk.Checkbutton(
            top_opt, text="Thumbnail", variable=self.download_thumb,
            font=("Consolas", 8), fg=self.theme["text"], bg=self.theme["panel"],
            selectcolor="#000000", activebackground=self.theme["panel"]
        ).pack(side="right")

        tk.Label(
            frame, text="Target Video URL (YT / FB / TikTok / IG / X):",
            font=("Consolas", 8), fg=self.theme["text"], bg=self.theme["panel"], anchor="w"
        ).pack(fill="x", padx=8)

        self.url_entry = tk.Entry(
            frame, font=("Consolas", 9), bg="#000000", fg=self.theme["fg"],
            insertbackground=self.theme["fg"], bd=1, relief="solid"
        )
        self.url_entry.pack(fill="x", padx=8, pady=2)

        fmt_frame = tk.Frame(frame, bg=self.theme["panel"])
        fmt_frame.pack(fill="x", padx=8, pady=2)
        tk.Label(fmt_frame, text="Format:", font=("Consolas", 8), fg=self.theme["text"], bg=self.theme["panel"]).pack(side="left")

        self.format_var = tk.StringVar(value="Best Video (MP4)")
        fmt_box = ttk.Combobox(
            fmt_frame, textvariable=self.format_var, state="readonly", width=18,
            values=["Best Video (MP4)", "720p HD (MP4)", "Audio Only (MP3)"]
        )
        fmt_box.pack(side="left", padx=4)

        tk.Button(
            fmt_frame, text="+ ADD QUEUE", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFFFFF", bd=0, padx=6, pady=2,
            command=self.manual_add_queue
        ).pack(side="right")

        tk.Label(
            frame, text="Batch Download Queue & Progress:",
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"], anchor="w"
        ).pack(fill="x", padx=8, pady=(4, 1))

        self.queue_listbox = tk.Listbox(
            frame, height=6, bg="#000000", fg=self.theme["text"],
            font=("Consolas", 8), bd=1, relief="solid", selectbackground=self.theme["accent"]
        )
        self.queue_listbox.pack(fill="both", expand=True, padx=8, pady=2)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=8, pady=2)

        # Quick Media Vault mini actions di bawah downloader
        vault_frame = tk.Frame(frame, bg=self.theme["panel"])
        vault_frame.pack(fill="x", padx=8, pady=(2, 6))

        tk.Button(
            vault_frame, text="📂 BUKA FOLDER DOWNLOADS", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, pady=3,
            command=lambda: os.startfile(DOWNLOAD_DIR)
        ).pack(fill="x")

    # ==========================================================================
    def _build_tab_win_cleaner(self):
        frame = tk.Frame(self.content_area, bg=self.theme["panel"], bd=1, relief="solid")
        self.tabs["[WIN CLEANER]"] = frame

        tk.Label(
            frame, text="=== WINDOWS CLEANER & OPTIMIZER PACK ===",
            font=("Consolas", 9, "bold"), fg=self.theme["fg"], bg=self.theme["panel"]
        ).pack(pady=(6, 2))

        clean_canvas_frame = tk.Frame(frame, bg=self.theme["panel"])
        clean_canvas_frame.pack(fill="both", expand=True, padx=6, pady=2)

        clean_actions = [
            ("1. Bersihkan TEMP Windows & AppData", self.run_clean_temp),
            ("2. Kosongkan Kotak Sampah (Recycle Bin)", self.run_clean_recycle),
            ("3. Bersihkan Cache Windows Update Lama", self.run_clean_winupdate),
            ("4. Bersihkan Cache Browser (Chrome/Edge/Firefox)", self.run_clean_browsers),
            ("5. Setel Skema Daya ke Performa Maksimal", self.run_power_plan),
            ("6. Reset Jaringan (Flush DNS & Winsock)", self.run_reset_network),
            ("7. Nonaktifkan Telemetri & Iklan Windows", self.run_debloat_privacy),
            ("8. Kelola Layanan Utama (Disable Update/Search)", self.run_disable_services),
            ("9. Jalankan Pemindaian Kesehatan CHKDSK", self.run_chkdsk_scan),
            ("10. Ekstrak Laporan Spesifikasi PC ke File", self.run_export_specs),
        ]

        for text, cmd_func in clean_actions:
            btn = tk.Button(
                clean_canvas_frame, text=text, font=("Consolas", 8),
                bg="#14261c", fg=self.theme["fg"], anchor="w", padx=8, pady=3,
                activebackground=self.theme["accent"], command=cmd_func
            )
            btn.pack(fill="x", pady=1)

    def run_clean_temp(self):
        def task():
            self.set_status("Membersihkan file TEMP Windows & User...")
            subprocess.run('del /f /s /q %SystemRoot%\\TEMP\\*.* >nul 2>&1', shell=True)
            subprocess.run('del /f /s /q "%USERPROFILE%\\AppData\\Local\\Temp\\*.*" >nul 2>&1', shell=True)
            self.set_status("Selesai membersihkan file sementara (TEMP).")
            messagebox.showinfo("Windows Cleaner", "File sementara (TEMP) berhasil dibersihkan!")
        threading.Thread(target=task, daemon=True).start()

    def run_clean_recycle(self):
        def task():
            self.set_status("Mengosongkan Recycle Bin...")
            subprocess.run('rd /s /q %systemdrive%\\$Recycle.bin >nul 2>&1', shell=True)
            self.set_status("Recycle Bin berhasil dikosongkan.")
            messagebox.showinfo("Windows Cleaner", "Kotak sampah (Recycle Bin) berhasil dikosongkan!")
        threading.Thread(target=task, daemon=True).start()

    def run_clean_winupdate(self):
        def task():
            self.set_status("Membersihkan Cache Windows Update...")
            subprocess.run('net stop wuauserv >nul 2>&1', shell=True)
            subprocess.run('del /f /s /q %SystemRoot%\\SoftwareDistribution\\Download\\*.* >nul 2>&1', shell=True)
            subprocess.run('net start wuauserv >nul 2>&1', shell=True)
            self.set_status("Cache Windows Update dibersihkan.")
            messagebox.showinfo("Windows Cleaner", "Cache Windows Update lama berhasil dihapus!")
        threading.Thread(target=task, daemon=True).start()

    def run_clean_browsers(self):
        def task():
            self.set_status("Membersihkan cache browser...")
            subprocess.run('taskkill /f /im chrome.exe >nul 2>&1', shell=True)
            subprocess.run('del /f /q /s "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache\\*.*" >nul 2>&1', shell=True)
            subprocess.run('taskkill /f /im msedge.exe >nul 2>&1', shell=True)
            subprocess.run('del /f /q /s "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache\\*.*" >nul 2>&1', shell=True)
            self.set_status("Cache browser selesai dibersihkan.")
            messagebox.showinfo("Windows Cleaner", "Cache Chrome & Edge berhasil disapu bersih!")
        threading.Thread(target=task, daemon=True).start()

    def run_power_plan(self):
        def task():
            self.set_status("Mengaktifkan skema High Performance...")
            subprocess.run('powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1', shell=True)
            self.set_status("Skema Performa Maksimal diaktifkan.")
            messagebox.showinfo("Optimizer", "Skema daya Windows berhasil diatur ke Performa Maksimal!")
        threading.Thread(target=task, daemon=True).start()

    def run_reset_network(self):
        def task():
            self.set_status("Melakukan Flush DNS & Winsock Reset...")
            subprocess.run('ipconfig /flushdns >nul 2>&1', shell=True)
            subprocess.run('netsh winsock reset >nul 2>&1', shell=True)
            subprocess.run('netsh int ip reset >nul 2>&1', shell=True)
            self.set_status("Jaringan berhasil di-refresh.")
            messagebox.showinfo("Network", "DNS cache dan tumpukan jaringan (Winsock) berhasil di-reset!")
        threading.Thread(target=task, daemon=True).start()

    def run_debloat_privacy(self):
        def task():
            self.set_status("Menonaktifkan telemetri & iklan...")
            subprocess.run('sc stop DiagTrack >nul 2>&1', shell=True)
            subprocess.run('sc config DiagTrack start= disabled >nul 2>&1', shell=True)
            subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul 2>&1', shell=True)
            self.set_status("Telemetri & iklan dimatikan.")
            messagebox.showinfo("Debloater", "Fitur telemetri dan pelacak iklan berhasil dinonaktifkan!")
        threading.Thread(target=task, daemon=True).start()

    def run_disable_services(self):
        def task():
            self.set_status("Menonaktifkan layanan berat (Defrag/Search/Update)...")
            subprocess.run('sc stop defragsvc >nul 2>&1', shell=True)
            subprocess.run('sc config defragsvc start= disabled >nul 2>&1', shell=True)
            subprocess.run('sc stop WSearch >nul 2>&1', shell=True)
            subprocess.run('sc config WSearch start= disabled >nul 2>&1', shell=True)
            self.set_status("Layanan utama Windows dikunci.")
            messagebox.showinfo("Services", "Layanan Optimize Drives & Windows Search berhasil dinonaktifkan!")
        threading.Thread(target=task, daemon=True).start()

    def run_chkdsk_scan(self):
        def task():
            self.set_status("Menjalankan pemindaian CHKDSK...")
            sys_drive = os.environ.get("SystemDrive", "C:")
            subprocess.run(f'chkdsk {sys_drive}', shell=True)
            self.set_status("Pemindaian CHKDSK selesai.")
            messagebox.showinfo("Diagnostics", "Pemeriksaan kesehatan disk selesai dijalankan!")
        threading.Thread(target=task, daemon=True).start()

    def run_export_specs(self):
        def task():
            logfile = "Spesifikasi_PC_D3D_Explorer.txt"
            self.set_status(f"Mengekstrak spesifikasi PC ke {logfile}...")
            with open(logfile, "w", encoding="utf-8") as f:
                f.write("========================================================\n")
                f.write("       LAPORAN SPESIFIKASI SISTEM - D3D EXPLORER        \n")
                f.write("             Generated by Mr.Rm19 (github.com/Rm19x)    \n")
                f.write("========================================================\n")
                f.write(f"Tanggal Audit : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
                f.write(f"Total RAM: {ram_gb} GB\n")
                f.write(f"CPU Cores: {psutil.cpu_count(logical=True)} Logical Cores\n")
            self.set_status(f"Spesifikasi berhasil diekstrak ke {logfile}")
            os.startfile(logfile)
            messagebox.showinfo("Diagnostics", f"Laporan spesifikasi berhasil disimpan ke:\n{logfile}")
        threading.Thread(target=task, daemon=True).start()

    # ==========================================================================
    def _build_tab_sys_net(self):
        frame = tk.Frame(self.content_area, bg=self.theme["panel"], bd=1, relief="solid")
        self.tabs["[SYS & NET]"] = frame

        tools_grid = tk.Frame(frame, bg=self.theme["panel"])
        tools_grid.pack(fill="x", padx=6, pady=4)

        tk.Button(
            tools_grid, text=" RAM TRIM", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, pady=4,
            command=self.clean_ram
        ).grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        tk.Button(
            tools_grid, text=" SCREENSHOT", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, pady=4,
            command=self.capture_screenshot
        ).grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        tk.Button(
            tools_grid, text=" SPEEDTEST", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, pady=4,
            command=self.run_speedtest_thread
        ).grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        tk.Button(
            tools_grid, text=" SCAN LAN", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, pady=4,
            command=self.scan_local_network_thread
        ).grid(row=1, column=1, sticky="ew", padx=2, pady=2)

        tools_grid.columnconfigure(0, weight=1)
        tools_grid.columnconfigure(1, weight=1)

        self.net_console = tk.Text(
            frame, height=5, bg="#000000", fg=self.theme["fg"],
            font=("Consolas", 8), bd=1, relief="solid"
        )
        self.net_console.pack(fill="x", padx=6, pady=2)
        self.net_console.insert("end", "[SYS & NET CONSOLE READY]\n")

        tk.Label(
            frame, text="Task Killer (Top RAM Processes):",
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"], anchor="w"
        ).pack(fill="x", padx=6, pady=(4, 1))

        tk_frame = tk.Frame(frame, bg=self.theme["panel"])
        tk_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.proc_listbox = tk.Listbox(
            tk_frame, height=5, bg="#000000", fg=self.theme["text"],
            font=("Consolas", 8), bd=1, relief="solid"
        )
        self.proc_listbox.pack(side="left", fill="both", expand=True)

        tk_btns = tk.Frame(tk_frame, bg=self.theme["panel"])
        tk_btns.pack(side="right", fill="y", padx=(4, 0))

        tk.Button(
            tk_btns, text=" List", font=("Consolas", 8),
            bg=self.theme["accent"], fg="#FFF", bd=0, width=7,
            command=self.refresh_process_list
        ).pack(pady=2)

        tk.Button(
            tk_btns, text=" KILL", font=("Consolas", 8, "bold"),
            bg="#880000", fg="#FFF", bd=0, width=7,
            command=self.kill_selected_process
        ).pack(pady=2)

        self.refresh_process_list()

    # ==========================================================================
    def _build_tab_config(self):
        frame = tk.Frame(self.content_area, bg=self.theme["panel"], bd=1, relief="solid")
        self.tabs["[D3D CONFIG]"] = frame

        tk.Label(
            frame, text="D3D Menu Transparency (Alpha):",
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"], anchor="w"
        ).pack(fill="x", padx=8, pady=(6, 2))

        self.alpha_slider = tk.Scale(
            frame, from_=0.3, to=1.0, resolution=0.05, orient="horizontal",
            bg=self.theme["panel"], fg=self.theme["text"], troughcolor="#000000",
            highlightthickness=0, command=self.update_transparency
        )
        self.alpha_slider.set(self.alpha_val)
        self.alpha_slider.pack(fill="x", padx=8)

        tk.Label(
            frame, text="D3D Color Theme:",
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"], anchor="w"
        ).pack(fill="x", padx=8, pady=(6, 2))

        self.theme_box = ttk.Combobox(
            frame, values=list(THEMES.keys()), state="readonly", font=("Consolas", 8)
        )
        self.theme_box.set(self.current_theme_name)
        self.theme_box.pack(fill="x", padx=8)
        self.theme_box.bind("<<ComboboxSelected>>", self.change_theme)

        hk_frame = tk.Frame(frame, bg=self.theme["panel"])
        hk_frame.pack(fill="x", padx=8, pady=8)

        tk.Label(
            hk_frame, text="Toggle Hotkey:",
            font=("Consolas", 8, "bold"), fg=self.theme["fg"], bg=self.theme["panel"]
        ).pack(side="left")

        self.hk_entry = tk.Entry(
            hk_frame, width=8, font=("Consolas", 8, "bold"),
            bg="#000000", fg=self.theme["fg"], justify="center"
        )
        self.hk_entry.insert(0, self.hotkey)
        self.hk_entry.pack(side="left", padx=4)

        tk.Button(
            hk_frame, text="SET", font=("Consolas", 8, "bold"),
            bg=self.theme["accent"], fg="#FFF", bd=0, padx=6,
            command=self.apply_new_hotkey
        ).pack(side="left")

        about_box = tk.Frame(frame, bg="#000000", bd=1, relief="solid")
        about_box.pack(fill="both", expand=True, padx=8, pady=6)

        tk.Label(
            about_box, text="D3D Menu Explorer by Mr.Rm19",
            font=("Consolas", 9, "bold"), fg=self.theme["fg"], bg="#000000"
        ).pack(pady=(6, 2))

        tk.Label(
            about_box, text="Merged with Windows Cleaner CLI Pack\nGitHub: https://github.com/Rm19x",
            font=("Consolas", 7), fg=self.theme["text"], bg="#000000"
        ).pack(pady=2)

        tk.Button(
            about_box, text="🌐 OPEN GITHUB",
            font=("Consolas", 8, "bold"), bg=self.theme["accent"], fg="#FFFFFF",
            bd=0, padx=8, pady=3, command=lambda: webbrowser.open(GITHUB_URL)
        ).pack(pady=6)

    # ==========================================================================
    def _clipboard_watcher_loop(self):
        while True:
            try:
                if self.sniffer_enabled.get():
                    clip = self.root.clipboard_get().strip()
                    if clip != self.last_clipboard:
                        self.last_clipboard = clip
                        match = URL_PATTERN.search(clip)
                        if match:
                            detected_url = match.group(1)
                            self.root.after(0, lambda u=detected_url: self._trigger_d3d_popup(u))
            except Exception:
                pass
            time.sleep(1.0)

    def _trigger_d3d_popup(self, url):
        if not self.is_visible:
            self.toggle_visibility()

        popup = tk.Toplevel(self.root)
        popup.title("D3D Intercept")
        popup.geometry("360x150+120+150")
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#050505", highlightbackground=self.theme["fg"], highlightthickness=2)

        tk.Label(
            popup, text=" [D3D LINK INTERCEPTED] ",
            font=("Consolas", 9, "bold"), fg=self.theme["fg"], bg="#050505"
        ).pack(pady=(8, 2))

        tk.Label(popup, text="Simpan video ini ke D3D_Downloads?", font=("Consolas", 8, "bold"), fg="#FFF", bg="#050505").pack(pady=2)
        short_url = url if len(url) < 42 else url[:39] + "..."
        tk.Label(popup, text=short_url, font=("Consolas", 7), fg=self.theme["text"], bg="#050505").pack(pady=2)

        btn_frame = tk.Frame(popup, bg="#050505")
        btn_frame.pack(pady=8)

        def accept():
            popup.destroy()
            self.enqueue_download(url, self.format_var.get())

        tk.Button(btn_frame, text="[ YES ]", bg="#008822", fg="#FFF", bd=0, padx=10, pady=4, command=accept, font=("Consolas", 8, "bold")).pack(side="left", padx=4)
        tk.Button(btn_frame, text="[ NO ]", bg="#770000", fg="#FFF", bd=0, padx=10, pady=4, command=popup.destroy, font=("Consolas", 8, "bold")).pack(side="left", padx=4)

    def manual_add_queue(self):
        url = self.url_entry.get().strip()
        if not url.startswith("http"):
            messagebox.showwarning("Invalid URL", "Masukkan link video yang valid!")
            return
        self.url_entry.delete(0, "end")
        self.enqueue_download(url, self.format_var.get())

    def enqueue_download(self, url, fmt):
        self.download_queue.put({"url": url, "format": fmt})
        self.queue_listbox.insert("end", f"[QUEUED] {fmt} | {url[:35]}...")
        self.set_status("Ditambahkan ke antrean download.")

    def _download_worker_loop(self):
        while True:
            item = self.download_queue.get()
            url, fmt = item["url"], item["format"]
            self.root.after(0, lambda: self.progress_var.set(0))

            def hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes", 0)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        self.root.after(0, lambda p=pct: self.progress_var.set(p))

            ydl_opts = {
                "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).50s.%(ext)s"),
                "progress_hooks": [hook],
                "writethumbnail": self.download_thumb.get(),
                "noplaylist": True,
                "quiet": True,
            }
            if fmt == "Audio Only (MP3)":
                ydl_opts["format"] = "bestaudio/best"
                ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
            elif fmt == "720p HD (MP4)":
                ydl_opts["format"] = "best[height<=720][ext=mp4]/best"
            else:
                ydl_opts["format"] = "best[ext=mp4]/best"

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.root.after(0, lambda: self.set_status("Download selesai!"))
            except Exception as e:
                self.root.after(0, lambda err=str(e)[:30]: self.set_status(f"Gagal: {err}"))

            self.download_queue.task_done()

    def _sys_monitor_loop(self):
        while True:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                now = time.time()
                net_now = psutil.net_io_counters()
                dt = max(now - self.last_net_time, 0.1)

                dl = ((net_now.bytes_recv - self.last_net.bytes_recv) / 1024) / dt
                ul = ((net_now.bytes_sent - self.last_net.bytes_sent) / 1024) / dt
                self.last_net, self.last_net_time = net_now, now

                txt = f"CPU: {cpu:.0f}% | RAM: {ram:.0f}% | DL: {dl:.1f} KB/s | UL: {ul:.1f} KB/s"
                self.root.after(0, lambda t=txt: self.lbl_sys_stats.config(text=t))
            except Exception:
                pass
            time.sleep(1.0)

    def clean_ram(self):
        before = psutil.virtual_memory().percent
        for proc in psutil.process_iter(["pid"]):
            try:
                h = ctypes.windll.kernel32.OpenProcess(0x001F0FFF, False, proc.info["pid"])
                if h:
                    ctypes.windll.psapi.EmptyWorkingSet(h)
                    ctypes.windll.kernel32.CloseHandle(h)
            except Exception:
                pass
        after = psutil.virtual_memory().percent
        self.set_status(f"RAM Trimmed: {before}% -> {after}%")
        messagebox.showinfo("RAM Trim", f"RAM dibersihkan! {before}% menjadi {after}%")

    def capture_screenshot(self):
        self.root.withdraw()
        time.sleep(0.3)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"D3D_{ts}.png")
        ImageGrab.grab().save(path)
        if self.is_visible:
            self.root.deiconify()
        self.set_status(f"Screenshot saved: D3D_{ts}.png")
        os.startfile(path)

    def run_speedtest_thread(self):
        self.net_console.delete("1.0", "end")
        self.net_console.insert("end", "[SPEEDTEST] Menguji jaringan...\n")
        def task():
            try:
                t0 = time.time()
                socket.create_connection(("1.1.1.1", 53), timeout=3)
                ping = (time.time() - t0) * 1000
                req = urllib.request.urlopen("https://speed.cloudflare.com/__down?bytes=3000000", timeout=8)
                data = req.read()
                mbps = (len(data) * 8) / ((time.time() - t0) * 1_000_000)
                res = f"Ping: {ping:.1f} ms | Speed: {mbps:.2f} Mbps\n"
                self.root.after(0, lambda: self.net_console.insert("end", res))
            except Exception as e:
                self.root.after(0, lambda: self.net_console.insert("end", f"Error: {e}\n"))
        threading.Thread(target=task, daemon=True).start()

    def scan_local_network_thread(self):
        self.net_console.delete("1.0", "end")
        self.net_console.insert("end", "[ARP SCAN] Memindai perangkat LAN...\n")
        def task():
            try:
                output = subprocess.check_output("arp -a", shell=True, text=True)
                lines = [l.strip() for l in output.splitlines() if "dynamic" in l.lower() or "static" in l.lower()]
                for l in lines[:6]:
                    self.root.after(0, lambda line=l: self.net_console.insert("end", f"{line}\n"))
            except Exception as e:
                self.root.after(0, lambda: self.net_console.insert("end", f"Error: {e}\n"))
        threading.Thread(target=task, daemon=True).start()

    def refresh_process_list(self):
        self.proc_listbox.delete(0, "end")
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                procs.append((p.info["memory_info"].rss / (1024 * 1024), p.info["pid"], p.info["name"]))
            except Exception:
                pass
        procs.sort(reverse=True)
        for mem, pid, name in procs[:20]:
            self.proc_listbox.insert("end", f"[{pid}] {name} ({mem:.0f} MB)")

    def kill_selected_process(self):
        sel = self.proc_listbox.curselection()
        if not sel:
            return
        pid = int(self.proc_listbox.get(sel[0]).split("]")[0].replace("[", ""))
        try:
            psutil.Process(pid).terminate()
            self.set_status(f"Process PID {pid} killed!")
            self.refresh_process_list()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membunuh proses: {e}")

    def switch_tab(self, name):
        for t_name, frame in self.tabs.items():
            frame.pack_forget()
            self.tab_buttons[t_name].config(bg=self.theme["panel"], fg=self.theme["text"])
        self.tabs[name].pack(fill="both", expand=True)
        self.tab_buttons[name].config(bg=self.theme["fg"], fg="#000000")

    def update_transparency(self, val):
        self.alpha_val = float(val)
        self.root.attributes("-alpha", self.alpha_val)

    def change_theme(self, event=None):
        selected = self.theme_box.get()
        if selected in THEMES:
            self.current_theme_name = selected
            self.theme = THEMES[selected]
            self.root.configure(bg=self.theme["bg"])
            self.header_canvas.config(bg=self.theme["bg"], highlightbackground=self.theme["fg"])
            self.title_label.config(fg=self.theme["fg"], bg=self.theme["bg"])
            self.sub_label.config(fg=self.theme["text"], bg=self.theme["bg"])
            self.lbl_sys_stats.config(fg=self.theme["fg"], bg=self.theme["panel"])
            self.status_bar.config(fg=self.theme["fg"], bg=self.theme["panel"])
            self.switch_tab("[D3D CONFIG]")

    def _bind_hotkey(self, key_name):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        try:
            keyboard.add_hotkey(key_name, lambda: self.root.after(0, self.toggle_visibility))
            self.hotkey = key_name
            self.sub_label.config(text=f"Hotkey: [{self.hotkey.upper()}] Hide/Show | github.com/Rm19x")
        except Exception as e:
            messagebox.showerror("Hotkey Error", f"Tombol tidak valid: {e}")

    def apply_new_hotkey(self):
        new_key = self.hk_entry.get().strip().lower()
        if new_key:
            self._bind_hotkey(new_key)
            self.set_status(f"Hotkey diubah ke [{new_key.upper()}]")

    def toggle_visibility(self):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.is_visible = True

    def _start_drag(self, event):
        self._drag_x, self._drag_y = event.x, event.y

    def _do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def set_status(self, msg):
        self.status_bar.config(text=f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _start_background_threads(self):
        threading.Thread(target=self._clipboard_watcher_loop, daemon=True).start()
        threading.Thread(target=self._download_worker_loop, daemon=True).start()
        threading.Thread(target=self._sys_monitor_loop, daemon=True).start()

    def clean_exit(self):
        self.matrix_running = False
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = D3DMenuExplorer(root)
    root.mainloop()