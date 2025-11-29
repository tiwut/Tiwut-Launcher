import tkinter as tk
from tkinter import ttk, font
import os
import requests
import zipfile
import subprocess
import threading
import shutil
import webbrowser
import sys
import json
import concurrent.futures
from math import floor, log
from PIL import Image, ImageTk
from urllib.parse import urlparse
from tkinterweb import HtmlFrame

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

class AppConfig:
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'TiwutLauncher')
    CONFIG_FILE_PATH = os.path.join(APP_DATA_DIR, 'config.json')
    ICON_CACHE_DIR = os.path.join(APP_DATA_DIR, 'icon_cache')
    INSTALL_SUBDIR = "TiwutApps"
    INSTALL_BASE_PATH = os.path.join(os.path.expanduser('~'), 'Documents', INSTALL_SUBDIR)
    DEFAULT_LIBRARY_URLS = ["https://launcher.tiwut.de/library.tiwut"]
    
    STYLE = {
        "theme": "clam",
        "background": "#121212",       
        "primary": "#1E1E1E",          
        "secondary": "#2D2D2D",        
        "accent": "#00E5FF",           
        "accent_hover": "#64F0FF",
        "text": "#FFFFFF",
        "text_secondary": "#B3B3B3",
        "disabled_bg": "#2C2C2C",
        "disabled_fg": "#666666",
        "font_family": "Segoe UI",
        "font_large_title": ("Segoe UI", 28, "bold"),
        "font_title": ("Segoe UI", 18, "bold"),
        "font_body": ("Segoe UI", 10),
        "font_body_bold": ("Segoe UI", 10, "bold"),
        "font_nav": ("Segoe UI", 11, "bold"),
    }

def format_bytes(size_bytes):
    if size_bytes <= 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def apply_windows_modern_blur(hwnd):
    if sys.platform != "win32": return
    try:
        dwmapi = ctypes.windll.dwmapi
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(1)), 4)
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(ctypes.c_int(2)), 4)
    except Exception: pass

class NativeDialog(tk.Toplevel):
    def __init__(self, parent, title, message, dialog_type="info"):
        super().__init__(parent)
        self.title(title); self.result = None
        self.configure(bg=AppConfig.STYLE["primary"])
        
        parent_x, parent_y = parent.winfo_rootx(), parent.winfo_rooty()
        parent_w, parent_h = parent.winfo_width(), parent.winfo_height()
        w, h = 420, 200
        self.geometry(f"{w}x{h}+{parent_x + (parent_w - w)//2}+{parent_y + (parent_h - h)//2}")
        
        self.resizable(False, False); self.transient(parent); self.grab_set()
        
        main_frame = ttk.Frame(self, padding=25, style='Primary.TFrame')
        main_frame.pack(expand=True, fill='both')
        
        ttk.Label(main_frame, text=message, wraplength=380, justify="left", style='Dialog.TLabel').pack(expand=True, fill='both')
        
        btn_frame = ttk.Frame(main_frame, style='Primary.TFrame')
        btn_frame.pack(side="bottom", fill="x", pady=(15, 0))
        
        if dialog_type == "askyesno": self._add_yes_no(btn_frame)
        else: self._add_ok(btn_frame)
        self.wait_window()

    def _add_ok(self, c): 
        ttk.Button(c, text="OK", command=self.destroy, style='Accent.TButton').pack(side="right")
    
    def _add_yes_no(self, c):
        def yes(): self.result = True; self.destroy()
        def no(): self.result = False; self.destroy()
        ttk.Button(c, text="Yes", command=yes, style='Accent.TButton').pack(side="right", padx=5)
        ttk.Button(c, text="No", command=no).pack(side="right")

class StatusInfoDisplay(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='App.TFrame', padding=(0, 10))
        self.status_lbl = ttk.Label(self, text="Initializing...", style='LightText.TLabel')
        self.status_lbl.pack(fill='x', pady=(0, 2))
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill='x', pady=(0, 2))
        self.info_lbl = ttk.Label(self, text="", style='ProgressInfo.TLabel')
        self.info_lbl.pack(fill='x')

    def update_full(self, percentage, status, info):
        if not self.winfo_exists(): return
        self.status_lbl['text'] = status
        self.progress_bar['value'] = percentage
        self.info_lbl['text'] = info
        if percentage >= 100: self.after(1500, self.destroy)

class IconManager:
    def __init__(self, root):
        self.root = root
        self.cache_dir = AppConfig.ICON_CACHE_DIR
        self.placeholder = None
        self.active_downloads = set()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def get_icon(self, app, callback, size=(180, 100)):
        icon_url = app.get("icon_url")
        if not icon_url: self._use_placeholder(callback, size); return
        
        filename = os.path.basename(urlparse(icon_url).path)
        cache_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(cache_path):
            self._load_image(cache_path, callback, size)
        else:
            self._use_placeholder(callback, size)
            if icon_url not in self.active_downloads:
                self.active_downloads.add(icon_url)
                self.executor.submit(self._download_icon, icon_url, cache_path, callback, size)

    def _download_icon(self, url, path, callback, size):
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f: shutil.copyfileobj(response.raw, f)
                self.root.after(0, self._load_image, path, callback, size)
        except Exception: pass
        finally:
            if url in self.active_downloads: self.active_downloads.remove(url)

    def _load_image(self, path, callback, size):
        try:
            with Image.open(path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                callback(photo)
        except Exception: self._use_placeholder(callback, size)

    def _use_placeholder(self, callback, size):
        if self.placeholder is None:
            img = Image.new('RGB', size, AppConfig.STYLE["secondary"])
            self.placeholder = ImageTk.PhotoImage(img)
        callback(self.placeholder)

class Page(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='App.TFrame')
        self.controller = controller
        self.grid(row=0, column=0, sticky="nsew")
    def on_show(self, **kwargs): pass

class AppGridViewPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        self.header = ttk.Frame(self, padding=(30, 25, 30, 15), style='App.TFrame')
        self.header.pack(fill="x")
        self.page_title = ttk.Label(self.header, text="", style='LargeTitle.TLabel')
        self.page_title.pack(side="left")
        
        search_frame = ttk.Frame(self.header, style='App.TFrame')
        search_frame.pack(side="right")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda n,i,m: self._filter_apps())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30, style='Search.TEntry').pack(ipady=5)

        container = ttk.Frame(self, style='App.TFrame')
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=AppConfig.STYLE["background"], bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        self.content_frame = ttk.Frame(self.canvas, style='App.TFrame', padding=30)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.content_frame.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        
        self.resize_timer = None
        self.bind("<Configure>", self._on_page_resize)
        
        self.all_apps_on_page = []
        self.apps_to_display = []
        self.animation_job = None

    def _on_content_configure(self, event): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event): self.canvas.itemconfig(self.canvas_window, width=event.width)
    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
    def _on_mousewheel(self, event):
        if self.winfo_viewable():
            if event.num == 5 or event.delta < 0: self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0: self.canvas.yview_scroll(-1, "units")

    def _set_app_list(self, apps):
        self.all_apps_on_page = sorted(apps, key=lambda x: x['name'])
        self.search_var.set("")
        self._filter_apps(animate=True)

    def _filter_apps(self, animate=True):
        term = self.search_var.get().lower()
        if not term: self.apps_to_display = self.all_apps_on_page
        else: self.apps_to_display = [a for a in self.all_apps_on_page if term in a['name'].lower()]
        self._repopulate_grid(animate=animate)

    def _on_page_resize(self, event):
        if self.resize_timer: self.after_cancel(self.resize_timer)
        self.resize_timer = self.after(150, lambda: self._repopulate_grid(animate=False))

    def _repopulate_grid(self, animate=True):
        if self.animation_job: self.after_cancel(self.animation_job); self.animation_job = None
        for w in self.content_frame.winfo_children(): w.destroy()
        
        if not self.apps_to_display:
            msg = "No applications found."
            if not self.controller.is_online and isinstance(self, DiscoverPage):
                msg = "Offline Mode: Cannot load new apps.\nCheck 'My Library' for installed apps."
            ttk.Label(self.content_frame, text=msg, style='LightText.TLabel').pack(pady=50)
            return

        width = self.canvas.winfo_width()
        if width < 100: width = self.winfo_width()
        cols = max(1, (width - 60) // 230)
        
        if animate: self._animate_card_entry(0, cols)
        else:
            for i, app in enumerate(self.apps_to_display):
                row, col = divmod(i, cols)
                self._create_card(app, row, col)

    def _animate_card_entry(self, index, cols):
        if index >= len(self.apps_to_display): return
        batch_size = 2
        for i in range(batch_size):
            if index + i >= len(self.apps_to_display): break
            row, col = divmod(index + i, cols)
            self._create_card(self.apps_to_display[index+i], row, col)
        self.animation_job = self.after(10, self._animate_card_entry, index + batch_size, cols)

    def _create_card(self, app, row, col):
        card = self.AppCard(self.content_frame, app, self.controller)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="n")

    class AppCard(ttk.Frame):
        def __init__(self, parent, app, controller):
            super().__init__(parent, style='Card.TFrame', padding=15)
            self.app = app; self.controller = controller
            self.bind("<Enter>", self._on_enter); self.bind("<Leave>", self._on_leave); self.bind("<Button-1>", self._show_details)

            self.icon_lbl = ttk.Label(self, style='Card.TLabel')
            self.icon_lbl.pack(pady=(0, 10))
            self.icon_lbl.bind("<Button-1>", self._show_details)
            self.controller.icon_manager.get_icon(app, self.set_icon)

            lbl = ttk.Label(self, text=app["name"], style='CardTitle.TLabel', anchor="center", wraplength=200)
            lbl.pack(fill="x", pady=(0, 10))
            lbl.bind("<Button-1>", self._show_details)

            ttk.Button(self, text="Details", command=self._show_details, style='Accent.TButton', cursor="hand2").pack(fill="x")

        def set_icon(self, img):
            if self.winfo_exists(): self.icon_lbl.configure(image=img); self.image = img
        def _on_enter(self, e): self.configure(style='CardHover.TFrame'); self.icon_lbl.configure(style='CardHover.TLabel')
        def _on_leave(self, e): self.configure(style='Card.TFrame'); self.icon_lbl.configure(style='Card.TLabel')
        def _show_details(self, e=None):
            src = self.controller.get_page_name(self.controller.current_frame)
            self.controller.show_frame("DetailsPage", app_data=self.app, source_page=src)

class DiscoverPage(AppGridViewPage):
    def on_show(self, **kwargs):
        self.page_title.config(text="Discover")
        self._set_app_list(self.controller.web_apps)

class LibraryPage(AppGridViewPage):
    def on_show(self, **kwargs):
        self.page_title.config(text="My Library")
        self.controller.scan_local_library()
        self._set_app_list(self.controller.local_apps)

class DetailsPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.app = None; self.source_page = "DiscoverPage"; self.progress_widget = None

    def on_show(self, app_data, source_page):
        self.app = app_data; self.source_page = source_page
        for w in self.winfo_children(): w.destroy()
        
        header = ttk.Frame(self, padding=(30, 20), style='App.TFrame')
        header.pack(fill="x")
        ttk.Button(header, text="← Back", command=lambda: self.controller.show_frame(self.source_page), style='Nav.TButton').pack(side="left")
        
        info_pane = ttk.Frame(self, padding=30, style='App.TFrame')
        info_pane.pack(fill="both", expand=True)

        top = ttk.Frame(info_pane, style='App.TFrame')
        top.pack(fill="x", pady=(0, 20))
        ttk.Label(top, text=self.app["name"], style='LargeTitle.TLabel').pack(side="left")
        
        actions = ttk.Frame(top, style='App.TFrame')
        actions.pack(side="right")
        self.btns = {}
        
        self.btns['install'] = ttk.Button(actions, text="Install", style='Accent.TButton', command=lambda: self.controller.install_app(self.app))
        self.btns['uninstall'] = ttk.Button(actions, text="Uninstall", command=lambda: self.controller.uninstall_app(self.app))
        self.btns['launch'] = ttk.Button(actions, text="Launch", style='Accent.TButton', command=lambda: self.controller.open_app(self.app))
        self.btns['shortcut'] = ttk.Button(actions, text="Create Shortcut", command=lambda: self.controller.create_shortcut(self.app))
        
        self._refresh_buttons()

        web_container = ttk.Frame(info_pane, style='Primary.TFrame', padding=2)
        web_container.pack(fill="both", expand=True)
        
        try:
            if self.controller.is_online and 'website_url' in self.app and self.app['website_url']:
                browser = HtmlFrame(web_container, messages_enabled=False, vertical_scrollbar=True)
                browser.load_website(self.app['website_url'])
                browser.pack(fill="both", expand=True)
            else:
                msg = "Offline Mode: Web preview unavailable." if not self.controller.is_online else "No website available."
                ttk.Label(web_container, text=msg, style='LightText.TLabel').pack(pady=20)
        except Exception as e:
            ttk.Label(web_container, text=f"Could not load preview: {e}", style='LightText.TLabel').pack(pady=20)

        bot = ttk.Frame(self, padding=20, style='App.TFrame')
        bot.pack(fill="x", side="bottom")
        if 'website_url' in self.app and self.app['website_url']:
            ttk.Button(bot, text="Open in Browser", command=lambda: self.controller.open_info_website(self.app)).pack(side="left")
        
        self.progress_container = ttk.Frame(bot, style='App.TFrame')
        self.progress_container.pack(side="right", fill="x", expand=True, padx=20)

    def _refresh_buttons(self):
        installed = self.controller.is_app_installed(self.app)
        for b in self.btns.values(): b.pack_forget()
        
        if installed:
            self.btns['launch'].pack(side="left", padx=5)
            if sys.platform == 'win32': self.btns['shortcut'].pack(side="left", padx=5)
            self.btns['uninstall'].pack(side="left", padx=5)
        else:
            self.btns['install'].pack(side="left", padx=5)

class SettingsPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        ttk.Label(self, text="Settings", style='LargeTitle.TLabel', padding=(30, 20)).pack(anchor="w")
        body = ttk.Frame(self, padding=30, style='App.TFrame')
        body.pack(fill="both", expand=True)
        
        ttk.Label(body, text="Library Sources", style='Title.TLabel').pack(anchor="w", pady=(0, 10))
        input_frame = ttk.Frame(body, style='App.TFrame')
        input_frame.pack(fill="x", pady=(0, 10))
        self.url_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.url_var, style='Search.TEntry').pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        ttk.Button(input_frame, text="Add", command=self._add, style='Accent.TButton').pack(side="left")

        list_frame = ttk.Frame(body, style='Primary.TFrame')
        list_frame.pack(fill="both", expand=True)
        self.lb = tk.Listbox(list_frame, bg=AppConfig.STYLE["primary"], fg=AppConfig.STYLE["text"], 
                             bd=0, highlightthickness=0, font=AppConfig.STYLE["font_body"], selectbackground=AppConfig.STYLE["accent"])
        self.lb.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.lb.yview)
        sb.pack(side="right", fill="y")
        self.lb.config(yscrollcommand=sb.set)

        act = ttk.Frame(body, style='App.TFrame')
        act.pack(fill="x", pady=15)
        ttk.Button(act, text="Remove Selected", command=self._remove).pack(side="left", padx=(0, 10))
        ttk.Button(act, text="Refresh Libraries", command=self._reload, style='Accent.TButton').pack(side="left")

    def on_show(self, **kwargs):
        self.lb.delete(0, tk.END)
        for url in self.controller.library_urls: self.lb.insert(tk.END, url)

    def _add(self):
        u = self.url_var.get().strip()
        if u and u not in self.controller.library_urls:
            self.controller.library_urls.append(u)
            self.controller.save_config(); self.on_show(); self.url_var.set("")

    def _remove(self):
        sel = self.lb.curselection()
        if not sel: return
        for i in reversed(sel): del self.controller.library_urls[i]
        self.controller.save_config(); self.on_show()

    def _reload(self):
        self.controller.reload_library(silent=False)


class AppStoreClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut App Store")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=AppConfig.STYLE["background"])
        
        self.setup_styles()
        self.load_config()
        self.icon_manager = IconManager(self)
        
        self.is_online = False
        self.web_apps = []
        self.local_apps = []
        
        
        self.scan_local_library()
        
        
        self.container = ttk.Frame(self, style='App.TFrame')
        self.container.pack(fill="both", expand=True)
        
        nav = ttk.Frame(self.container, width=240, style='Primary.TFrame')
        nav.pack(side="left", fill="y"); nav.pack_propagate(False)
        self._build_nav(nav)
        
        self.content = ttk.Frame(self.container, style='App.TFrame')
        self.content.pack(side="right", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1); self.content.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F in (DiscoverPage, LibraryPage, DetailsPage, SettingsPage):
            self.frames[F.__name__] = F(self.content, self)
            
        self.show_frame("DiscoverPage")
        
        self.after(10, lambda: apply_windows_modern_blur(ctypes.windll.user32.GetParent(self.winfo_id()) if sys.platform=="win32" else None))
        
        
        threading.Thread(target=self.load_web_library_background, daemon=True).start()
        self.download_app_icon()

    def setup_styles(self):
        s = ttk.Style(); s.theme_use('clam'); S = AppConfig.STYLE
        s.configure('.', background=S["background"], foreground=S["text"], borderwidth=0)
        s.configure('App.TFrame', background=S["background"])
        s.configure('Primary.TFrame', background=S["primary"])
        s.configure('Card.TFrame', background=S["primary"], relief='flat')
        s.configure('CardHover.TFrame', background=S["secondary"])
        s.configure('Card.TLabel', background=S["primary"])
        s.configure('CardHover.TLabel', background=S["secondary"])
        s.configure('TLabel', background=S["background"], foreground=S["text"], font=S["font_body"])
        s.configure('LargeTitle.TLabel', font=S["font_large_title"])
        s.configure('Title.TLabel', font=S["font_title"])
        s.configure('CardTitle.TLabel', background=S["primary"], font=S["font_body_bold"])
        s.configure('Dialog.TLabel', background=S["primary"])
        s.configure('LightText.TLabel', foreground=S["text_secondary"])
        s.configure('ProgressInfo.TLabel', foreground=S["accent"], font=S["font_nav"])
        s.configure('TButton', font=S["font_body_bold"], padding=8, background=S["secondary"], foreground=S["text"], borderwidth=0)
        s.map('TButton', background=[('active', '#404040')])
        s.configure('Accent.TButton', background=S["accent"], foreground='#000000')
        s.map('Accent.TButton', background=[('active', S["accent_hover"]), ('disabled', S["disabled_bg"])], foreground=[('disabled', S["disabled_fg"])])
        s.configure('Nav.TButton', font=S["font_nav"], padding=15, background=S["primary"], foreground=S["text_secondary"], anchor="w")
        s.map('Nav.TButton', background=[('active', S["secondary"]), ('selected', S["background"])], foreground=[('selected', S["accent"])])
        s.configure('Search.TEntry', fieldbackground=S["secondary"], foreground=S["text"], insertcolor=S["text"], borderwidth=0)
        s.configure('Vertical.TScrollbar', background=S["secondary"], troughcolor=S["background"], borderwidth=0, arrowsize=0)
        s.map('Vertical.TScrollbar', background=[('active', S["accent"])])

    def _build_nav(self, parent):
        ttk.Label(parent, text="TIWUT", font=("Segoe UI", 24, "bold"), foreground=AppConfig.STYLE["accent"], background=AppConfig.STYLE["primary"]).pack(pady=40, padx=25, anchor="w")
        self.nav_btns = {}
        for lbl, page in [("Discover", "DiscoverPage"), ("My Library", "LibraryPage"), ("Settings", "SettingsPage")]:
            b = ttk.Button(parent, text=lbl, style='Nav.TButton', command=lambda p=page: self.show_frame(p))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_btns[page] = b

    def show_frame(self, page_name, **kwargs):
        self.current_frame = self.frames[page_name]
        for name, b in self.nav_btns.items():
            b.state(['!selected'] if name != page_name else ['selected'])
        self.current_frame.on_show(**kwargs)
        self.current_frame.tkraise()

    def get_page_name(self, frame): return next((n for n, f in self.frames.items() if f == frame), None)


    def load_config(self):
        try:
            with open(AppConfig.CONFIG_FILE_PATH, 'r') as f:
                self.library_urls = json.load(f).get("library_urls", AppConfig.DEFAULT_LIBRARY_URLS)
        except Exception:
            self.library_urls = AppConfig.DEFAULT_LIBRARY_URLS; self.save_config()

    def save_config(self):
        with open(AppConfig.CONFIG_FILE_PATH, 'w') as f: json.dump({"library_urls": self.library_urls}, f)

    def scan_local_library(self):
        """Scans the installation directory for existing apps (works offline)"""
        self.local_apps = []
        if not os.path.exists(AppConfig.INSTALL_BASE_PATH): return
        
        for item in os.listdir(AppConfig.INSTALL_BASE_PATH):
            app_dir = os.path.join(AppConfig.INSTALL_BASE_PATH, item)
            if os.path.isdir(app_dir):
                
                meta_path = os.path.join(app_dir, 'app_info.json')
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r') as f:
                            self.local_apps.append(json.load(f))
                    except: pass
                else:
                    
                    self.local_apps.append({"name": item, "download_url": "", "website_url": "", "icon_url": ""})

    def load_web_library_background(self):
        """Fetches the web library and then attempts to fix local missing metadata"""
        try:
            apps = {}
            for url in self.library_urls:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                for line in r.text.splitlines():
                    p = line.strip().split(";")
                    if len(p) >= 3:
                        apps[p[0]] = {"name": p[0], "download_url": p[1], "website_url": p[2], "icon_url": p[3] if len(p)>3 else None}
            self.web_apps = list(apps.values())
            self.is_online = True
            
            
            self.sync_missing_metadata(apps)
            
            
            if isinstance(self.current_frame, DiscoverPage):
                self.after(0, lambda: self.frames["DiscoverPage"].on_show())
        except Exception as e:
            print(f"Offline mode: {e}")
            self.is_online = False

    def sync_missing_metadata(self, web_apps_dict):
        """Self-healing: updates local app_info.json for apps installed by older versions"""
        updates_made = False
        for local_app in self.local_apps:
            
            if not local_app.get("icon_url") and local_app["name"] in web_apps_dict:
                matched_data = web_apps_dict[local_app["name"]]
                local_app.update(matched_data)
                
                
                app_dir = os.path.join(AppConfig.INSTALL_BASE_PATH, local_app["name"])
                if os.path.exists(app_dir):
                    with open(os.path.join(app_dir, "app_info.json"), "w") as f:
                        json.dump(local_app, f)
                    updates_made = True
        
        if updates_made:
            
            if isinstance(self.current_frame, LibraryPage):
                self.after(0, lambda: self.frames["LibraryPage"].on_show())

    def reload_library(self, silent=True):
        self.scan_local_library()
        try:
            apps = {}
            for url in self.library_urls:
                r = requests.get(url, timeout=5)
                r.raise_for_status()
                for line in r.text.splitlines():
                    p = line.strip().split(";")
                    if len(p) >= 3:
                        apps[p[0]] = {"name": p[0], "download_url": p[1], "website_url": p[2], "icon_url": p[3] if len(p)>3 else None}
            self.web_apps = list(apps.values())
            self.is_online = True
            self.sync_missing_metadata(apps)
            if not silent: NativeDialog(self, "Success", "Library reloaded.")
        except Exception as e:
            self.is_online = False
            if not silent: NativeDialog(self, "Error", f"Could not connect: {e}")
        
        self.show_frame("DiscoverPage")

    def is_app_installed(self, app): 
        return os.path.exists(os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]))
    
    def download_app_icon(self):
        path = os.path.join(AppConfig.APP_DATA_DIR, "icon.ico")
        if not os.path.exists(path):
            threading.Thread(target=lambda: requests.get("https://tiwut.de/icon.ico").content, daemon=True).start()

    def open_info_website(self, app): webbrowser.open(app.get('website_url', ''))
    
    def open_app(self, app):
        exe = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"], "main.exe")
        if os.path.exists(exe): subprocess.Popen(exe, cwd=os.path.dirname(exe))
        else: NativeDialog(self, "Error", "Executable 'main.exe' not found.", "error")

    def create_shortcut(self, app):
        if sys.platform != 'win32': return
        try:
            target = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"], "main.exe")
            link = os.path.join(os.path.expanduser('~'), 'Desktop', f"{app['name']}.lnk")
            vbs = os.path.join(AppConfig.APP_DATA_DIR, 's.vbs')
            with open(vbs, 'w') as f:
                f.write(f'Set o=WScript.CreateObject("WScript.Shell")\nSet s=o.CreateShortcut("{link}")\ns.TargetPath="{target}"\ns.WorkingDirectory="{os.path.dirname(target)}"\ns.Save')
            subprocess.call(['cscript', '//Nologo', vbs])
            os.remove(vbs); NativeDialog(self, "Success", "Shortcut created.")
        except Exception as e: NativeDialog(self, "Error", str(e), "error")

    def install_app(self, app):
        dp = self.frames["DetailsPage"]
        if dp.progress_widget: return
        dp.progress_widget = StatusInfoDisplay(dp.progress_container); dp.progress_widget.pack(fill='x')
        dp.btns['install'].state(['disabled'])
        threading.Thread(target=self._install_thread, args=(app,), daemon=True).start()

    def _install_thread(self, app):
        dp = self.frames["DetailsPage"]
        try:
            dest = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]); os.makedirs(dest, exist_ok=True)
            
            with open(os.path.join(dest, "app_info.json"), "w") as f:
                json.dump(app, f)

            zip_file = os.path.join(dest, "pkg.zip")
            
            with requests.get(app["download_url"], stream=True) as r:
                total = int(r.headers.get('content-length', 0)); down = 0
                with open(zip_file, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk); down += len(chunk)
                        pct = (down/total)*100 if total else 0
                        self.after(0, lambda p=pct, d=down, t=total: dp.progress_widget.update_full(p, f"Downloading...", f"{format_bytes(d)} / {format_bytes(t)}"))

            self.after(0, lambda: dp.progress_widget.update_full(100, "Extracting...", ""))
            with zipfile.ZipFile(zip_file, 'r') as z: z.extractall(dest)
            os.remove(zip_file)
            
            self.scan_local_library()
            self.after(0, lambda: [dp.on_show(app, dp.source_page), NativeDialog(self, "Success", "Installed!")])
        except Exception as e:
            self.after(0, lambda: [NativeDialog(self, "Error", str(e)), dp.progress_widget.destroy(), dp.btns['install'].state(['!disabled'])])

    def uninstall_app(self, app):
        if NativeDialog(self, "Confirm", f"Uninstall {app['name']}?", "askyesno").result:
            try:
                shutil.rmtree(os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]))
                self.scan_local_library()
                self.frames["DetailsPage"].on_show(app, self.frames["DetailsPage"].source_page)
                NativeDialog(self, "Success", "Uninstalled.")
            except Exception as e: NativeDialog(self, "Error", str(e))

if __name__ == "__main__":
    for p in [AppConfig.APP_DATA_DIR, AppConfig.INSTALL_BASE_PATH, AppConfig.ICON_CACHE_DIR]: os.makedirs(p, exist_ok=True)
    AppStoreClient().mainloop()