import tkinter as tk
from tkinter import ttk
from tkinter import font
import os
import requests
import zipfile
import subprocess
import threading
import shutil
import webbrowser
import sys
from math import floor, log
from PIL import Image, ImageTk
from urllib.parse import urlparse
import json

class AppConfig:
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'TiwutLauncher')
    CONFIG_FILE_PATH = os.path.join(APP_DATA_DIR, 'config.json')
    ICON_CACHE_DIR = os.path.join(APP_DATA_DIR, 'icon_cache')
    INSTALL_SUBDIR = "TiwutApps"
    INSTALL_BASE_PATH = os.path.join(os.path.expanduser('~'), 'Documents', INSTALL_SUBDIR)
    DEFAULT_LIBRARY_URLS = ["https://launcher.tiwut.de/library.tiwut"]
    STYLE = {
        "theme": "clam",
        "background": "#2E2E2E",
        "primary": "#3C3C3C",
        "secondary": "#505050",
        "accent": "#0078D7",
        "accent_hover": "#0098FF",
        "text": "#FFFFFF",
        "text_secondary": "#B0B0B0",
        "disabled_bg": "#555555",
        "disabled_fg": "#9E9E9E",
        "font_family": "Segoe UI",
        "font_large_title": ("Segoe UI", 24, "bold"),
        "font_title": ("Segoe UI", 14, "bold"),
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

class NativeDialog(tk.Toplevel):
    def __init__(self, parent, title, message, dialog_type="info"):
        super().__init__(parent)
        self.title(title); self.result = None
        self.configure(bg=AppConfig.STYLE["background"])
        parent_x, parent_y, parent_w, parent_h = parent.winfo_x(), parent.winfo_y(), parent.winfo_width(), parent.winfo_height()
        dialog_w, dialog_h = 400, 180
        self.geometry(f"{dialog_w}x{dialog_h}+{parent_x + (parent_w - dialog_w) // 2}+{parent_y + (parent_h - dialog_h) // 2}")
        self.resizable(False, False); self.transient(parent); self.grab_set()
        main_frame = ttk.Frame(self, padding=20, style='App.TFrame'); main_frame.pack(expand=True, fill='both')
        ttk.Label(main_frame, text=message, wraplength=360, justify="left", style='LightText.TLabel').pack(expand=True, fill='both')
        button_frame = ttk.Frame(main_frame, style='App.TFrame'); button_frame.pack(side="bottom", fill="x", pady=(10, 0))
        if dialog_type == "askyesno": self._add_yes_no_buttons(button_frame)
        else: self._add_ok_button(button_frame)
        self.wait_window()
    def _add_ok_button(self, c): ttk.Button(c, text="OK", command=self.destroy, style='Accent.TButton').pack()
    def _add_yes_no_buttons(self, c):
        def on_yes(): self.result = True; self.destroy()
        def on_no(): self.result = False; self.destroy()
        bc = ttk.Frame(c, style='App.TFrame'); bc.pack()
        ttk.Button(bc, text="Yes", command=on_yes, style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(bc, text="No", command=on_no).pack(side="left", padx=5)

class StatusProgressBar(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, style='App.TFrame', padding=(0, 10))
        self.status_label = ttk.Label(self, text="Initializing...", style='LightText.TLabel'); self.status_label.pack(fill='x')
        self.progress_bar = ttk.Progressbar(self, orient='horizontal', mode='determinate'); self.progress_bar.pack(fill='x', pady=5)
        self.info_label = ttk.Label(self, text="", style='SecondaryText.TLabel'); self.info_label.pack(fill='x')
    def update_full(self, percentage, status, info):
        self.progress_bar['value'] = percentage; self.status_label['text'] = status; self.info_label['text'] = info
        if percentage >= 100: self.after(2000, self.destroy)

class IconManager:
    def __init__(self, root):
        self.root = root
        self.cache_dir = AppConfig.ICON_CACHE_DIR
        self.placeholder = None
        self.active_downloads = set()
    def get_icon(self, app, callback, size=(180, 100)):
        icon_url = app.get("icon_url")
        if not icon_url: self._use_placeholder(callback, size); return
        filename = os.path.basename(urlparse(icon_url).path)
        cache_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(cache_path):
            self._load_image_from_path(cache_path, callback, size)
        else:
            self._use_placeholder(callback, size)
            if icon_url not in self.active_downloads:
                self.active_downloads.add(icon_url)
                threading.Thread(target=self._download_icon, args=(icon_url, cache_path, callback, size), daemon=True).start()
    def _download_icon(self, url, path, callback, size):
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f: shutil.copyfileobj(response.raw, f)
                self.root.after(0, self._load_image_from_path, path, callback, size)
        except requests.RequestException as e:
            print(f"Error downloading icon {url}: {e}")
        finally:
            if url in self.active_downloads:
                self.active_downloads.remove(url)
    def _load_image_from_path(self, path, callback, size):
        try:
            with Image.open(path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(img)
                callback(photo_image)
        except Exception:
            self._use_placeholder(callback, size)
    def _use_placeholder(self, callback, size):
        if self.placeholder is None:
            ph_img = Image.new('RGB', size, AppConfig.STYLE["secondary"])
            self.placeholder = ImageTk.PhotoImage(ph_img)
        callback(self.placeholder)

class Page(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style='App.TFrame')
        self.controller = controller
        self.grid(row=0, column=0, sticky="nsew")
    def on_show(self, **kwargs):
        pass

class AppGridViewPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.header = ttk.Frame(self, padding=(25, 20, 25, 10), style='App.TFrame'); self.header.pack(fill="x")
        self.page_title = ttk.Label(self.header, text="Page Title", style='LargeTitle.TLabel'); self.page_title.pack(side="left", anchor="w")
        
        search_frame = ttk.Frame(self.header, style='App.TFrame')
        search_frame.pack(side="right", anchor="e")
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self._filter_apps())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30, style='Search.TEntry')
        search_entry.pack(side="left", ipady=4)
        
        frame_container = tk.Frame(self, bg=AppConfig.STYLE["background"]); frame_container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame_container, bg=AppConfig.STYLE["background"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(frame_container, orient="vertical", command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas, style='App.TFrame', padding=25)
        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True); self.scrollbar.pack(side="right", fill="y")
        
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.bind("<Configure>", self._repopulate_grid)
        
        self.all_apps_on_page = []
        self.apps_to_display = []
        self.animation_job = None

        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
    def _set_app_list(self, apps):
        self.all_apps_on_page = sorted(apps, key=lambda x: x['name'])
        self.search_var.set("")
        self._filter_apps()

    def _filter_apps(self):
        search_term = self.search_var.get().lower()
        if not search_term:
            self.apps_to_display = self.all_apps_on_page
        else:
            self.apps_to_display = [app for app in self.all_apps_on_page if search_term in app['name'].lower()]
        self._repopulate_grid()

    def _repopulate_grid(self, event=None):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
            
        for widget in self.content_frame.winfo_children(): widget.destroy()
        
        if not self.apps_to_display:
            ttk.Label(self.content_frame, text="No applications found.", style='LightText.TLabel').pack(pady=50)
            return
        
        container_width = self.winfo_width() - 70 
        card_width = 220
        cols = max(1, container_width // card_width)
        
        self._animate_card_entry(0, cols)

    def _animate_card_entry(self, index, cols):
        if index >= len(self.apps_to_display):
            self.animation_job = None
            return

        app = self.apps_to_display[index]
        row, col = divmod(index, cols)
        
        card = self.AppCard(self.content_frame, app, self.controller)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="n")
        
        self.animation_job = self.after(40, self._animate_card_entry, index + 1, cols)

    class AppCard(ttk.Frame):
        def __init__(self, parent, app, controller):
            super().__init__(parent, style='Card.TFrame', padding=10)
            self.app = app; self.controller = controller
            
            self.bind("<Button-1>", self._show_details)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

            self.icon_label = ttk.Label(self, style='App.TFrame')
            self.icon_label.pack(pady=5)
            self.controller.icon_manager.get_icon(app, self.set_icon)
            self.icon_label.bind("<Button-1>", self._show_details)

            app_name = ttk.Label(self, text=app["name"], style='CardTitle.TLabel', anchor="center")
            app_name.pack(fill="x", pady=(10, 5))
            app_name.bind("<Button-1>", self._show_details)

            self.view_btn = ttk.Button(self, text="View Details", command=self._show_details, style='Accent.TButton')
            self.view_btn.pack(pady=(0, 5))
        
        def set_icon(self, photo_image):
            if self.winfo_exists():
                self.icon_image = photo_image
                self.icon_label.configure(image=self.icon_image)

        def _on_enter(self, e):
            self.configure(style='CardHover.TFrame')

        def _on_leave(self, e):
            self.configure(style='Card.TFrame')
        
        def _show_details(self, e=None):
            source = self.controller.get_page_name(self.controller.current_frame)
            self.controller.show_frame("DetailsPage", app_data=self.app, source_page=source)

class DiscoverPage(AppGridViewPage):
    def on_show(self, **kwargs):
        self.page_title.config(text="Discover New Apps")
        self._set_app_list(self.controller.get_all_apps())

class LibraryPage(AppGridViewPage):
    def on_show(self, **kwargs):
        self.page_title.config(text="My Installed Apps")
        self._set_app_list(self.controller.get_installed_apps())

class DetailsPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.app = None
        self.source_page = "DiscoverPage" 

    def on_show(self, app_data, source_page):
        self.app = app_data
        self.source_page = source_page
        self._populate_view()

    def _populate_view(self):
        for widget in self.winfo_children(): widget.destroy()
        header_frame = ttk.Frame(self, padding=(25, 20, 25, 10), style='App.TFrame')
        header_frame.pack(fill="x", anchor="n")
        back_button = ttk.Button(header_frame, text="< Back", command=lambda: self.controller.show_frame(self.source_page))
        back_button.pack(side="left", anchor="n")
        title_frame = ttk.Frame(self, padding=(25, 10), style='App.TFrame')
        title_frame.pack(fill="x", anchor="n")
        ttk.Label(title_frame, text=self.app["name"], style='LargeTitle.TLabel').pack(side="left")
        self.action_frame = ttk.Frame(title_frame, style='App.TFrame'); self.action_frame.pack(side="right")
        self.install_btn = ttk.Button(self.action_frame, text="Install", style='Accent.TButton', command=lambda: self.controller.install_app(self.app))
        self.uninstall_btn = ttk.Button(self.action_frame, text="Uninstall", command=lambda: self.controller.uninstall_app(self.app))
        self.launch_btn = ttk.Button(self.action_frame, text="Launch", style='Accent.TButton', command=lambda: self.controller.open_app(self.app))
        self.shortcut_btn = ttk.Button(self.action_frame, text="Create Shortcut", command=lambda: self.controller.create_shortcut(self.app))
        
        content_frame = ttk.Frame(self, padding=25, style='App.TFrame')
        content_frame.pack(fill="both", expand=True)
        ttk.Label(content_frame, text="About this App", style='Title.TLabel').pack(anchor="w", pady=(10,0))
        ttk.Label(content_frame, text="For detailed information, please visit the official website.", style='LightText.TLabel').pack(anchor="w", pady=(2, 10))
        ttk.Button(content_frame, text="Open Website", command=lambda: self.controller.open_info_website(self.app)).pack(anchor="w", pady=10)
        self.progress_container = ttk.Frame(self, style='App.TFrame', padding=25)
        self.progress_container.pack(fill="x", side="bottom")
        self._update_action_buttons()

    def _update_action_buttons(self):
        is_installed = self.controller.is_app_installed(self.app)
        self.install_btn.pack_forget()
        self.uninstall_btn.pack_forget()
        self.launch_btn.pack_forget()
        self.shortcut_btn.pack_forget()

        if is_installed:
            self.uninstall_btn.pack(side="left", padx=5)
            self.launch_btn.pack(side="left", padx=5)
            if sys.platform == 'win32':
                self.shortcut_btn.pack(side="left", padx=5)
        else:
            self.install_btn.pack(side="left", padx=5)

class SettingsPage(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        header = ttk.Frame(self, padding=(25, 20, 25, 10), style='App.TFrame')
        header.pack(fill="x")
        ttk.Label(header, text="Settings", style='LargeTitle.TLabel').pack(side="left", anchor="w")

        content = ttk.Frame(self, padding=25, style='App.TFrame')
        content.pack(fill="both", expand=True)

        ttk.Label(content, text="Manage Library URLs", style='Title.TLabel').pack(anchor="w", pady=(0, 10))
        
        add_frame = ttk.Frame(content, style='App.TFrame')
        add_frame.pack(fill="x", pady=5)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(add_frame, textvariable=self.url_var, style='Search.TEntry')
        url_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))
        
        add_button = ttk.Button(add_frame, text="Add Library", command=self._add_url, style='Accent.TButton')
        add_button.pack(side="left")

        list_frame = ttk.Frame(content, style='App.TFrame')
        list_frame.pack(fill="both", expand=True, pady=10)

        self.library_listbox = tk.Listbox(
            list_frame, 
            bg=AppConfig.STYLE["secondary"], 
            fg=AppConfig.STYLE["text"],
            font=AppConfig.STYLE["font_body"],
            borderwidth=0,
            highlightthickness=0,
            selectbackground=AppConfig.STYLE["accent"]
        )
        self.library_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.library_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.library_listbox.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(content, style='App.TFrame')
        button_frame.pack(fill="x", pady=5)

        remove_button = ttk.Button(button_frame, text="Remove Selected", command=self._remove_selected_url)
        remove_button.pack(side="left", padx=(0, 10))

        reload_button = ttk.Button(button_frame, text="Reload App Library", command=self._reload_library, style='Accent.TButton')
        reload_button.pack(side="left")

    def on_show(self, **kwargs):
        self._populate_list()

    def _populate_list(self):
        self.library_listbox.delete(0, tk.END)
        for url in self.controller.library_urls:
            self.library_listbox.insert(tk.END, url)

    def _add_url(self):
        new_url = self.url_var.get().strip()
        if new_url and new_url not in self.controller.library_urls:
            self.controller.library_urls.append(new_url)
            self.controller.save_config()
            self._populate_list()
            self.url_var.set("")
        elif not new_url:
            NativeDialog(self, "Info", "Please enter a URL.", "info")
        else:
            NativeDialog(self, "Info", "This URL is already in the list.", "info")

    def _remove_selected_url(self):
        selected_indices = self.library_listbox.curselection()
        if not selected_indices:
            NativeDialog(self, "Info", "Please select a URL to remove.", "info")
            return
        
        for index in sorted(selected_indices, reverse=True):
            del self.controller.library_urls[index]
            
        self.controller.save_config()
        self._populate_list()

    def _reload_library(self):
        self.controller.reload_library()
        NativeDialog(self, "Success", "The app library has been reloaded.", "info")

class AppStoreClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.setup_icon()
        self.title("Tiwut App Store")
        self.geometry("1100x750"); self.minsize(800, 600)
        self.configure(bg=AppConfig.STYLE["background"])
        self.setup_styles()
        self.icon_manager = IconManager(self)
        self.load_config()
        self.all_apps = self.load_library()
        main_container = ttk.Frame(self, style='App.TFrame'); main_container.pack(fill="both", expand=True)
        nav_rail = ttk.Frame(main_container, width=200, style='Primary.TFrame'); nav_rail.pack(side="left", fill="y"); nav_rail.pack_propagate(False)
        self.content_area = ttk.Frame(main_container, style='App.TFrame'); self.content_area.pack(side="right", fill="both", expand=True)
        self.content_area.grid_rowconfigure(0, weight=1); self.content_area.grid_columnconfigure(0, weight=1)
        self.frames = {}; self.nav_buttons = {}
        self._create_navigation(nav_rail); self._create_pages()
        self.show_frame("DiscoverPage")

    def setup_icon(self):
        icon_url = "https://tiwut.de/icon.ico"
        icon_name = "app_icon.ico"
        icon_path = os.path.join(AppConfig.APP_DATA_DIR, icon_name)
        if not os.path.exists(icon_path):
            try:
                response = requests.get(icon_url, timeout=10)
                response.raise_for_status()
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
            except requests.RequestException as e:
                print(f"Error downloading app icon: {e}")
                return
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Error setting app icon: {e}")

    def setup_styles(self):
        s = ttk.Style(); s.theme_use(AppConfig.STYLE["theme"]); S = AppConfig.STYLE
        s.configure('App.TFrame', background=S["background"])
        s.configure('Primary.TFrame', background=S["primary"])
        s.configure('Card.TFrame', background=S["primary"], borderwidth=1, relief='solid', bordercolor=S["primary"])
        s.configure('CardHover.TFrame', background=S["secondary"], borderwidth=1, relief='solid', bordercolor=S["accent"])
        s.configure('TLabel', background=S["background"], foreground=S["text"], font=S["font_body"])
        s.configure('LightText.TLabel', background=S["background"], foreground=S["text"], font=S["font_body"])
        s.configure('SecondaryText.TLabel', background=S["background"], foreground=S["text_secondary"], font=S["font_body"])
        s.configure('LargeTitle.TLabel', background=S["background"], foreground=S["text"], font=S["font_large_title"])
        s.configure('Title.TLabel', background=S["background"], foreground=S["text"], font=S["font_title"])
        s.configure('CardTitle.TLabel', background=S["primary"], foreground=S["text"], font=S["font_body_bold"])
        s.configure('TButton', font=S["font_body_bold"], padding=10, relief='flat'); s.map('TButton', background=[('active', S["secondary"])])
        s.configure('Accent.TButton', foreground=S["text"], background=S["accent"]); s.map('Accent.TButton', background=[('active', S["accent_hover"]), ('disabled', S["disabled_bg"])], foreground=[('disabled', S["disabled_fg"])])
        s.configure('Nav.TButton', font=S["font_nav"], padding=(20, 10), background=S["primary"], foreground=S["text_secondary"], borderwidth=0)
        s.map('Nav.TButton', background=[('active', S["secondary"]), ('selected', S["background"])], foreground=[('selected', S["text"])])
        s.configure('Search.TEntry', fieldbackground=S["secondary"], foreground=S["text"], bordercolor=S["secondary"], insertcolor=S["text"])

    def _create_navigation(self, nav_rail):
        ttk.Label(nav_rail, text="TIWUT STORE", font=("Segoe UI", 16, "bold"), background=AppConfig.STYLE["primary"], foreground=AppConfig.STYLE["accent"]).pack(pady=25, padx=10)
        for text, page_name in [("Discover", "DiscoverPage"), ("My Library", "LibraryPage"), ("Settings", "SettingsPage")]:
            btn = ttk.Button(nav_rail, text=text, style='Nav.TButton', command=lambda p=page_name: self.show_frame(p))
            btn.pack(fill="x", padx=10, pady=2); self.nav_buttons[page_name] = btn

    def _create_pages(self):
        for F in (DiscoverPage, LibraryPage, DetailsPage, SettingsPage): 
            self.frames[F.__name__] = F(self.content_area, self)

    def show_frame(self, page_name, **kwargs):
        self.current_frame = self.frames[page_name]
        for name, button in self.nav_buttons.items(): button.state(['!selected']); button.state(['selected'] if name == page_name else [])
        self.current_frame.on_show(**kwargs); self.current_frame.tkraise()
    
    def get_page_name(self, f): return next((name for name, frame in self.frames.items() if frame == f), None)

    def load_config(self):
        try:
            with open(AppConfig.CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
                self.library_urls = config.get("library_urls", AppConfig.DEFAULT_LIBRARY_URLS)
        except (FileNotFoundError, json.JSONDecodeError):
            self.library_urls = AppConfig.DEFAULT_LIBRARY_URLS
            self.save_config()

    def save_config(self):
        with open(AppConfig.CONFIG_FILE_PATH, 'w') as f:
            json.dump({"library_urls": self.library_urls}, f, indent=4)

    def load_library(self):
        apps_dict = {}
        errors = []
        for url in self.library_urls:
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                for line in r.text.splitlines():
                    if not line.strip(): continue
                    parts = line.strip().split(";")
                    if len(parts) >= 3:
                        app = {
                            "name": parts[0], 
                            "download_url": parts[1], 
                            "website_url": parts[2]
                        }
                        if len(parts) >= 4: app["icon_url"] = parts[3]
                        
                        if app["name"] not in apps_dict:
                            apps_dict[app["name"]] = app
            except requests.RequestException as e:
                errors.append(f"Could not load library from:\n{url}\nError: {e}\n")
        
        if errors:
            NativeDialog(self, "Network Error", "\n".join(errors))
        
        if not apps_dict and not errors:
             NativeDialog(self, "Library Empty", "No applications found in the configured libraries.")
        
        return list(apps_dict.values())

    def reload_library(self):
        self.all_apps = self.load_library()
        self.frames["DiscoverPage"].on_show()
        self.frames["LibraryPage"].on_show()
        if isinstance(self.current_frame, DetailsPage):
            updated_app_data = next((app for app in self.all_apps if app["name"] == self.current_frame.app["name"]), None)
            if updated_app_data:
                self.current_frame.on_show(app_data=updated_app_data, source_page=self.current_frame.source_page)

    def get_all_apps(self): return self.all_apps
    def get_installed_apps(self): return [app for app in self.all_apps if self.is_app_installed(app)]
    def is_app_installed(self, app): return os.path.exists(os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]))

    def open_info_website(self, app):
        try: 
            webbrowser.open(app['website_url'])
        except Exception as e: 
            NativeDialog(self, "Error", f"Could not open website:\n{e}", "error")

    def create_shortcut(self, app):
        try:
            if sys.platform != 'win32':
                NativeDialog(self, "Unsupported", "Desktop shortcuts are only supported on Windows.", "error")
                return

            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            shortcut_path = os.path.join(desktop_path, f"{app['name']}.lnk")
            target_path = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"], "main.exe")
            working_dir = os.path.dirname(target_path)
            
            shortcut_path_vbs = shortcut_path.replace('\\', '\\\\')
            target_path_vbs = target_path.replace('\\', '\\\\')
            working_dir_vbs = working_dir.replace('\\', '\\\\')
            icon_path_vbs = target_path_vbs 

            vbs_script = f'''
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{shortcut_path_vbs}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{target_path_vbs}"
            oLink.WorkingDirectory = "{working_dir_vbs}"
            oLink.IconLocation = "{icon_path_vbs}, 0"
            oLink.Save
            '''
            script_path = os.path.join(AppConfig.APP_DATA_DIR, 'sc.vbs')
            with open(script_path, 'w', encoding='utf-8') as f: f.write(vbs_script)
            subprocess.call(['cscript', '//Nologo', script_path], shell=False)
            os.remove(script_path)
            NativeDialog(self, "Success", f"Shortcut for {app['name']} created on your Desktop.")
        except Exception as e:
            NativeDialog(self, "Error", f"Could not create shortcut:\n{e}", "error")

    def install_app(self, app):
        dp = self.frames["DetailsPage"]; self.progress_bar = StatusProgressBar(dp.progress_container); self.progress_bar.pack(fill='x')
        dp.install_btn.state(['disabled'])
        threading.Thread(target=self._download_task, args=(app,), daemon=True).start()

    def _download_task(self, app):
        dp = self.frames["DetailsPage"]
        try:
            self.after(0, lambda: self.progress_bar.update_full(0, "Connecting...", ""))
            app_dir = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]); os.makedirs(app_dir, exist_ok=True)
            zip_path = os.path.join(app_dir, "app.zip")
            with requests.get(app["download_url"], stream=True, timeout=15) as r:
                r.raise_for_status(); total = int(r.headers.get('content-length', 0)); downloaded = 0
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk); downloaded += len(chunk)
                        if total > 0:
                            prog = (downloaded / total) * 100; info = f"{format_bytes(downloaded)} / {format_bytes(total)}"
                            self.after(0, lambda p=prog, i=info: self.progress_bar.update_full(p, f"Downloading {app['name']}...", i))
            self.after(0, lambda: self.progress_bar.update_full(100, "Extracting files...", ""));
            with zipfile.ZipFile(zip_path, 'r') as zf: zf.extractall(app_dir)
            os.remove(zip_path)
            self.after(0, lambda: [
                dp.on_show(app_data=app, source_page=dp.source_page),
                self.frames["LibraryPage"].on_show()
            ])
            NativeDialog(self, "Success", f"{app['name']} was installed successfully.")
        except Exception as e:
            NativeDialog(self, "Error", f"Installation failed:\n{e}", "error")
            self.after(0, dp.install_btn.state(['!disabled']))

    def uninstall_app(self, app):
        dp = self.frames["DetailsPage"]
        if NativeDialog(self, "Confirm", f"Uninstall {app['name']}?", "askyesno").result:
            try: 
                shutil.rmtree(os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"]))
                NativeDialog(self, "Success", f"{app['name']} was uninstalled.")
                self.after(0, lambda: [
                    dp.on_show(app_data=app, source_page=dp.source_page),
                    self.frames["LibraryPage"].on_show()
                ])
            except Exception as e: 
                NativeDialog(self, "Error", f"Failed to uninstall:\n{e}", "error")

    def open_app(self, app):
        exe = os.path.join(AppConfig.INSTALL_BASE_PATH, app["name"], "main.exe")
        if os.path.exists(exe):
            try: 
                subprocess.Popen(exe, cwd=os.path.dirname(exe))
            except Exception as e: 
                NativeDialog(self, "Error", f"Failed to launch app:\n{e}", "error")
        else: 
            NativeDialog(self, "Error", "'main.exe' not found!", "error")

if __name__ == "__main__":
    for path in [AppConfig.APP_DATA_DIR, AppConfig.INSTALL_BASE_PATH, AppConfig.ICON_CACHE_DIR]:
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                tk.Tk().withdraw()
                from tkinter import messagebox
                messagebox.showerror("Startup Error", f"Could not create required directory:\n{path}\n\nError: {e}")
                sys.exit(1)
                
    app = AppStoreClient()
    app.mainloop()