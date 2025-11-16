import tkinter as tk
from tkinter import font
import os
import requests
import zipfile
import subprocess
import threading
import random
import shutil
import webview
import time

# --- Style-Konfiguration ---
STYLE = {
    "background": "#000000",
    "transparent_color": "lime green",
    "foreground": "#e0e0e0",
    "primary_neon": "#ff00ff",
    "secondary_neon": "#00ffff",
    "tertiary_neon": "#fcee0c",
    "widget_bg": "#1a1a1a",
    "disabled_fg": "#555555",
    "font_main": ("Consolas", 12),
    "font_title": ("Consolas", 28, "bold"),
    "font_button": ("Consolas", 14, "bold"),
}

# --- Helper für gerundete Rechtecke ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
              x2, y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
              x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y2 - radius, x1, y1 + radius,
              x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- Scrollbare Frame-Klasse ---
class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.config(bg=STYLE["background"])
        canvas = tk.Canvas(self, bg=STYLE["background"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview, bg=STYLE["background"], troughcolor=STYLE["background"], activebackground=STYLE["widget_bg"])
        self.scrollable_frame = tk.Frame(canvas, bg=STYLE["background"])
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

# --- ProgressBar mit sanfter Animation ---
class ProgressBar(tk.Frame):
    def __init__(self, master, height=20):
        super().__init__(master, bg=STYLE["background"])
        self.status_label = tk.Label(self, text="Initializing...", font=("Consolas", 12), bg=STYLE["background"], fg=STYLE["secondary_neon"])
        self.status_label.pack()
        self.canvas = tk.Canvas(self, height=height, bg=STYLE["widget_bg"], highlightthickness=0)
        self.canvas.pack(fill='x', expand=True, padx=50)
        self.progress_rect = create_rounded_rect(self.canvas, 2, 2, 2, height - 2, radius=8, fill=STYLE["tertiary_neon"], width=0)
        self.info_label = tk.Label(self, text="", font=("Consolas", 10), bg=STYLE["background"], fg=STYLE["tertiary_neon"])
        self.info_label.pack()
        self.current_percentage = 0
        self.target_percentage = 0
        self._animate_progress()
    def update_full(self, percentage, status_text, info_text):
        self.target_percentage = percentage
        self.status_label.config(text=status_text)
        self.info_label.config(text=info_text)
    def _animate_progress(self):
        if abs(self.target_percentage - self.current_percentage) > 0.1:
            self.current_percentage += (self.target_percentage - self.current_percentage) * 0.2
            width = self.canvas.winfo_width()
            if width > 5:
                new_width = (width - 4) * (self.current_percentage / 100)
                self.canvas.coords(self.progress_rect, 2, 2, max(2, new_width), self.canvas.winfo_height() - 2)
        self.after(20, self._animate_progress)

def format_bytes(size):
    power = 1024; n = 0; power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size >= power and n < len(power_labels) - 1:
        size /= power; n += 1
    return f"{size:.1f} {power_labels[n]}B"

# --- KORRIGIERTER RoundedButton ---
class RoundedButton(tk.Frame):
    def __init__(self, master, text, command, width, height, radius=25):
        # HIER WAR DER FEHLER: `w` und `h` wurden zu `width` und `height` korrigiert.
        super().__init__(master, width=width, height=height, bg=STYLE["background"])
        self.command = command
        self.is_disabled = False
        self.canvas = tk.Canvas(self, width=width, height=height, bg=STYLE["background"], highlightthickness=0)
        self.canvas.pack()
        self.shape = create_rounded_rect(self.canvas, 0, 0, width, height, radius, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"], width=2)
        self.text_label = self.canvas.create_text(width/2, height/2, text=text, font=STYLE["font_button"], fill=STYLE["primary_neon"])
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)
    def _on_click(self, event):
        if self.command and not self.is_disabled: self.command()
    def _on_hover(self, event):
        if not self.is_disabled: self.canvas.itemconfig(self.shape, fill=STYLE["primary_neon"]); self.canvas.itemconfig(self.text_label, fill=STYLE["widget_bg"])
    def _on_leave(self, event):
        if not self.is_disabled: self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"]); self.canvas.itemconfig(self.text_label, fill=STYLE["primary_neon"])
    def set_state(self, state=None):
        if state == tk.DISABLED: self.is_disabled = True; self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["disabled_fg"]); self.canvas.itemconfig(self.text_label, fill=STYLE["disabled_fg"])
        elif state == tk.NORMAL: self.is_disabled = False; self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"]); self.canvas.itemconfig(self.text_label, fill=STYLE["primary_neon"])

class CustomDialog(tk.Toplevel):
    def __init__(self, master, title, message):
        super().__init__(master); self.title(title); self.message=message; self.result=None; self.overrideredirect(True); self.config(bg=STYLE["widget_bg"],bd=2,relief="solid"); self.attributes('-topmost',True); mx,my,mw,mh=master.winfo_x(),master.winfo_y(),master.winfo_width(),master.winfo_height(); self.geometry(f"400x200+{mx+(mw-400)//2}+{my+(mh-200)//2}"); tk.Label(self,text=title,font=("Consolas",14,"bold"),bg=STYLE["widget_bg"],fg=STYLE["secondary_neon"]).pack(pady=(10,0)); tk.Label(self,text=message,font=STYLE["font_main"],bg=STYLE["widget_bg"],fg=STYLE["foreground"],wraplength=380).pack(pady=20,padx=10,expand=True,fill="both"); self.button_frame=tk.Frame(self,bg=STYLE["widget_bg"]); self.button_frame.pack(pady=10)
    def showinfo(self): RoundedButton(self.button_frame,"OK",self.destroy,100,50).pack(); self.wait_window()
    def showerror(self): RoundedButton(self.button_frame,"OK",self.destroy,100,50).pack(); self.wait_window()
    def askyesno(self):
        def on_yes(): self.result=True; self.destroy()
        def on_no(): self.result=False; self.destroy()
        RoundedButton(self.button_frame,"Yes",on_yes,100,50).pack(side="left",padx=10); RoundedButton(self.button_frame,"No",on_no,100,50).pack(side="left",padx=10); self.wait_window(); return self.result

class TiwutLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.geometry("900x700")
        self.attributes("-transparentcolor", STYLE["transparent_color"])
        self.config(bg=STYLE["transparent_color"])
        self.bg_canvas = tk.Canvas(self, bg=STYLE["transparent_color"], highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self.draw_background)
        self.content_frame = tk.Frame(self, bg=STYLE["background"])
        self.bg_canvas.create_window(0, 0, anchor="nw", window=self.content_frame)
        self.title_bar = tk.Frame(self.content_frame, bg=STYLE["widget_bg"], bd=0)
        self.title_bar.pack(expand=0, fill='x')
        tk.Label(self.title_bar, text="Tiwut Launcher", bg=STYLE["widget_bg"], fg=STYLE["secondary_neon"], font=("Consolas", 10)).pack(side='left', padx=10)
        tk.Button(self.title_bar, text='X', command=self.destroy, bg=STYLE["widget_bg"], fg=STYLE["primary_neon"], relief="flat", font=("Consolas", 10, "bold")).pack(side='right', padx=5)
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)
        self.main_frame = tk.Frame(self.content_frame, bg=STYLE["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.library_url = "https://launcher.tiwut.de/library.tiwut"
        self.apps = self.load_library_from_url()
        self.create_home_page()
    def draw_background(self, event=None):
        self.bg_canvas.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        create_rounded_rect(self.bg_canvas, 0, 0, width, height, 30, fill=STYLE["background"])
        self.bg_canvas.create_window(0, 0, anchor="nw", window=self.content_frame, width=width, height=height)
    def start_move(self, event): self.x = event.x; self.y = event.y
    def stop_move(self, event): self.x = None; self.y = None
    def on_motion(self, event): self.geometry(f"+{self.winfo_x() + (event.x - self.x)}+{self.winfo_y() + (event.y - self.y)}")
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
    def load_library_from_url(self):
        apps = []
        try:
            r = requests.get(self.library_url)
            r.raise_for_status()
            for line in r.text.splitlines():
                if line.strip():
                    parts = line.strip().split(";")
                    if len(parts) == 3: apps.append({"name": parts[0], "download_url": parts[1], "website_url": parts[2]})
        except requests.exceptions.RequestException as e: CustomDialog(self, "Network Error", f"Could not load library:\n{e}").showerror(); self.quit()
        return apps
    def create_home_page(self):
        self.clear_main_frame()
        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=40, padx=20, fill="both", expand=True)
        tk.Label(container, text="T I W U T", font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=(0, 40))
        search_container = tk.Frame(container, bg=STYLE["background"])
        search_container.pack(pady=10, fill='x', padx=50)
        search_canvas = tk.Canvas(search_container, height=50, bg=STYLE["background"], highlightthickness=0)
        search_canvas.pack(fill='x')
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var, font=STYLE["font_main"], bg=STYLE["widget_bg"], fg=STYLE["foreground"], insertbackground=STYLE["primary_neon"], relief=tk.FLAT, bd=0)
        placeholder = "Type to search..."
        self.search_entry.insert(0, placeholder); self.search_entry.config(fg='grey')
        def on_focus_in(e):
            if self.search_entry.get() == placeholder: self.search_entry.delete(0, "end"); self.search_entry.config(fg=STYLE["foreground"])
        def on_focus_out(e):
            if not self.search_entry.get(): self.search_entry.insert(0, placeholder); self.search_entry.config(fg='grey')
        self.search_entry.bind("<FocusIn>", on_focus_in); self.search_entry.bind("<FocusOut>", on_focus_out)
        def on_frame_configure(e): search_canvas.delete("all"); create_rounded_rect(search_canvas, 0, 0, e.width, e.height, 25, fill=STYLE["widget_bg"], outline=STYLE["secondary_neon"], width=2); self.search_entry.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.9)
        search_container.bind("<Configure>", on_frame_configure)
        self.search_var.trace("w", self.search_apps)
        self.app_list_frame = ScrollableFrame(container)
        self.app_list_frame.pack(pady=20, fill="both", expand=True)
        self.display_random_apps()
    def display_random_apps(self):
        self._populate_app_list(random.sample(self.apps, min(len(self.apps), 15)), "Featured Apps")
    def search_apps(self, *args):
        search_term = self.search_var.get().lower()
        if not search_term or search_term == "type to search...": self.display_random_apps(); return
        results = [app for app in self.apps if search_term in app["name"].lower()]
        self._populate_app_list(results, "Search Results")
    def _populate_app_list(self, apps_to_show, title):
        frame = self.app_list_frame.scrollable_frame
        for widget in frame.winfo_children(): widget.destroy()
        if not apps_to_show and title == "Search Results": tk.Label(frame, text="No results found.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack(); return
        tk.Label(frame, text=title, font=("Consolas", 18, "bold"), bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0, 20))
        for app in apps_to_show: RoundedButton(frame, app["name"], lambda a=app: self.show_app_details(a), 400, 50).pack(pady=8)
    def show_app_details(self, app):
        self.clear_main_frame()
        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=20, padx=20, fill="both", expand=True)
        RoundedButton(container, "< Back", self.create_home_page, 150, 50).pack(anchor="nw", pady=(0, 20))
        tk.Label(container, text=app["name"], font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=20)
        button_frame = tk.Frame(container, bg=STYLE["background"])
        button_frame.pack(pady=20)
        is_installed = os.path.exists(os.path.join(os.getcwd(), app["name"]))
        self.install_button = RoundedButton(button_frame, "Install", lambda: self.install_app(app), 150, 50)
        self.uninstall_button = RoundedButton(button_frame, "Uninstall", lambda: self.uninstall_app(app), 150, 50)
        self.open_button = RoundedButton(button_frame, "Open", lambda: self.open_app(app), 150, 50)
        self.info_button = RoundedButton(button_frame, "View Details", lambda: self.open_info_website(app), 150, 50)
        self.install_button.pack(side=tk.LEFT, padx=10)
        self.uninstall_button.pack(side=tk.LEFT, padx=10)
        self.open_button.pack(side=tk.LEFT, padx=10)
        self.info_button.pack(side=tk.LEFT, padx=10)
        self.update_buttons(is_installed)
        tk.Label(container, text="Click 'View Details' to open app info in a new window.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["secondary_neon"], wraplength=500).pack(pady=40)
    def update_buttons(self, is_installed):
        if is_installed: self.install_button.set_state(tk.DISABLED); self.uninstall_button.set_state(tk.NORMAL); self.open_button.set_state(tk.NORMAL)
        else: self.install_button.set_state(tk.NORMAL); self.uninstall_button.set_state(tk.DISABLED); self.open_button.set_state(tk.DISABLED)
    def open_info_website(self, app):
        try: webview.create_window(f"Details - {app['name']}", app['website_url'], width=800, height=600); webview.start()
        except Exception as e: CustomDialog(self, "Error", f"Could not open window:\n{e}").showerror()
    def install_app(self, app):
        self.progress_bar = ProgressBar(self.main_frame)
        self.progress_bar.pack(fill='x', side='bottom', pady=10)
        self.install_button.set_state(tk.DISABLED)
        threading.Thread(target=self._download_and_extract, args=(app,)).start()
    def _download_and_extract(self, app):
        try:
            self.after(0, self.progress_bar.update_full, 0, "Connecting to Server...", "")
            app_dir = os.path.join(os.getcwd(), app["name"]); os.makedirs(app_dir, exist_ok=True)
            zip_path = os.path.join(app_dir, "app.zip")
            with requests.get(app["download_url"], stream=True) as r:
                r.raise_for_status(); total_size = int(r.headers.get('content-length', 0)); downloaded = 0
                start_time = time.time(); last_update_time = start_time; downloaded_since_update = 0
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk); downloaded += len(chunk); downloaded_since_update += len(chunk)
                        current_time = time.time()
                        if total_size > 0 and (current_time - last_update_time) > 0.2:
                            progress = (downloaded / total_size) * 100
                            elapsed_time = current_time - last_update_time
                            speed = downloaded_since_update / elapsed_time if elapsed_time > 0 else 0
                            status = "Downloading App..."
                            info = f"{format_bytes(speed)}/s  |  {format_bytes(downloaded)} / {format_bytes(total_size)}"
                            self.after(0, self.progress_bar.update_full, progress, status, info)
                            last_update_time = current_time; downloaded_since_update = 0
            self.after(0, self.progress_bar.update_full, 100, "Extracting Files...", "Please wait...")
            time.sleep(0.5)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(app_dir)
            os.remove(zip_path)
            self.after(0, self.progress_bar.update_full, 100, "Installation Complete", "")
            time.sleep(1)
            self.update_buttons(True)
            CustomDialog(self, "Success", f"{app['name']} was installed successfully.").showinfo()
        except Exception as e: CustomDialog(self, "Error", f"An error occurred during installation:\n{e}").showerror(); self.install_button.set_state(tk.NORMAL)
        finally:
            if hasattr(self, 'progress_bar'): self.after(100, self.progress_bar.destroy)
    def uninstall_app(self, app):
        if CustomDialog(self, "Confirm Uninstall", f"Are you sure you want to uninstall {app['name']}?").askyesno():
            try: shutil.rmtree(os.path.join(os.getcwd(), app["name"])); CustomDialog(self, "Success", f"{app['name']} was uninstalled.").showinfo(); self.update_buttons(False)
            except Exception as e: CustomDialog(self, "Error", f"Failed to uninstall:\n{e}").showerror()
    def open_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"], "main.exe")
        if os.path.exists(app_path):
            try: subprocess.Popen(app_path, cwd=os.path.dirname(app_path))
            except Exception as e: CustomDialog(self, "Error", f"Failed to launch app:\n{e}").showerror()
        else: CustomDialog(self, "Error", "'main.exe' not found in app directory!").showerror()

if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()