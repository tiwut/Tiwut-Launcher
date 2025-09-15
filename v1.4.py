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

# --- Style-Konfiguration für das Cyberpunk-Design ---
STYLE = {
    "background": "#000000",
    "foreground": "#e0e0e0",
    "primary_neon": "#ff00ff",   # Leuchtendes Pink
    "secondary_neon": "#00ffff", # Cyan / Türkis
    "tertiary_neon": "#fcee0c",    # Neongelb
    "widget_bg": "#1a1a1a",
    "disabled_fg": "#555555",
    "font_main": ("Consolas", 12),
    "font_title": ("Consolas", 28, "bold"),
    "font_button": ("Consolas", 14, "bold"),
}

# --- Helper Funktion um gerundete Rechtecke auf einem Canvas zu zeichnen ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
              x2, y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
              x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y2 - radius, x1, y1 + radius,
              x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- Stark abgerundeter, benutzerdefinierter Button ---
class RoundedButton(tk.Frame):
    def __init__(self, master, text, command, width, height, radius=25):
        super().__init__(master, width=width, height=height)
        # HIER WAR DER FEHLERURSPRUNG. Die folgende Zeile ruft die ECHTE config-Methode auf, was jetzt funktioniert.
        self.config(bg=STYLE["background"]) 
        self.command = command
        self.is_disabled = False
        
        self.canvas = tk.Canvas(self, width=width, height=height, bg=STYLE["background"], highlightthickness=0)
        self.canvas.pack()
        
        self.shape = create_rounded_rect(self.canvas, 0, 0, width, height, radius, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"], width=2)
        self.text = self.canvas.create_text(width/2, height/2, text=text, font=STYLE["font_button"], fill=STYLE["primary_neon"])
        
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)

    def _on_click(self, event):
        if self.command and not self.is_disabled:
            self.command()

    def _on_hover(self, event):
        if not self.is_disabled:
            self.canvas.itemconfig(self.shape, fill=STYLE["primary_neon"])
            self.canvas.itemconfig(self.text, fill=STYLE["widget_bg"])
    
    def _on_leave(self, event):
        if not self.is_disabled:
            self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"])
            self.canvas.itemconfig(self.text, fill=STYLE["primary_neon"])
            
    # KORREKTUR: Methode umbenannt von 'config' zu 'set_state'
    def set_state(self, state=None):
        if state == tk.DISABLED:
            self.is_disabled = True
            self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["disabled_fg"])
            self.canvas.itemconfig(self.text, fill=STYLE["disabled_fg"])
        elif state == tk.NORMAL:
            self.is_disabled = False
            self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"])
            self.canvas.itemconfig(self.text, fill=STYLE["primary_neon"])

# --- Benutzerdefinierte Dialogfenster ---
class CustomDialog(tk.Toplevel):
    def __init__(self, master, title, message):
        super().__init__(master)
        self.title(title)
        self.message = message
        self.result = None

        self.overrideredirect(True)
        self.config(bg=STYLE["widget_bg"], borderwidth=2, relief="solid")
        self.attributes('-topmost', True)

        master_x, master_y, master_w, master_h = master.winfo_x(), master.winfo_y(), master.winfo_width(), master.winfo_height()
        self.geometry(f"400x200+{master_x + (master_w - 400)//2}+{master_y + (master_h - 200)//2}")
        
        tk.Label(self, text=title, font=("Consolas", 14, "bold"), bg=STYLE["widget_bg"], fg=STYLE["secondary_neon"]).pack(pady=(10,0))
        tk.Label(self, text=message, font=STYLE["font_main"], bg=STYLE["widget_bg"], fg=STYLE["foreground"], wraplength=380).pack(pady=20, padx=10, expand=True, fill="both")
        
        self.button_frame = tk.Frame(self, bg=STYLE["widget_bg"])
        self.button_frame.pack(pady=10)
        
    def showinfo(self):
        RoundedButton(self.button_frame, "OK", self.destroy, width=100, height=50).pack()
        self.wait_window()

    def showerror(self):
        RoundedButton(self.button_frame, "OK", self.destroy, width=100, height=50).pack()
        self.wait_window()
        
    def askyesno(self):
        def on_yes(): self.result = True; self.destroy()
        def on_no(): self.result = False; self.destroy()
        RoundedButton(self.button_frame, "Yes", on_yes, width=100, height=50).pack(side="left", padx=10)
        RoundedButton(self.button_frame, "No", on_no, width=100, height=50).pack(side="left", padx=10)
        self.wait_window()
        return self.result

# --- Hauptklasse des Launchers ---
class TiwutLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut Launcher")
        
        self.overrideredirect(True)
        self.geometry("900x700")
        self.config(bg=STYLE["background"])
        
        self.title_bar = tk.Frame(self, bg=STYLE["widget_bg"], relief='raised', bd=0)
        self.title_bar.pack(expand=0, fill='x')
        
        tk.Label(self.title_bar, text="Tiwut Launcher", bg=STYLE["widget_bg"], fg=STYLE["secondary_neon"], font=("Consolas", 10)).pack(side='left', padx=10)
        tk.Button(self.title_bar, text='X', command=self.destroy, bg=STYLE["widget_bg"], fg=STYLE["primary_neon"], relief="flat", font=("Consolas", 10, "bold")).pack(side='right', padx=5)

        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.on_motion)
        
        self.main_frame = tk.Frame(self, bg=STYLE["background"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.library_url = "https://launcher.tiwut.de/library.tiwut"
        self.apps = self.load_library_from_url()
        self.create_home_page()

    def start_move(self, event): self.x = event.x; self.y = event.y
    def stop_move(self, event): self.x = None; self.y = None
    def on_motion(self, event):
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    def load_library_from_url(self):
        apps = []
        try:
            response = requests.get(self.library_url)
            response.raise_for_status()
            for line in response.text.splitlines():
                if line.strip():
                    parts = line.strip().split(";")
                    if len(parts) == 3: apps.append({"name": parts[0], "download_url": parts[1], "website_url": parts[2]})
        except requests.exceptions.RequestException as e:
            CustomDialog(self, "Network Error", f"Could not load the app library:\n{e}").showerror()
            self.quit()
        return apps

    def create_home_page(self):
        self.clear_main_frame()
        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=40, padx=20, fill="both", expand=True)

        tk.Label(container, text="T I W U T", font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=(0, 40))

        search_frame = tk.Frame(container, bg=STYLE["background"])
        search_frame.pack(pady=20, fill='x', padx=50)
        search_canvas = tk.Canvas(search_frame, height=50, bg=STYLE["background"], highlightthickness=0)
        search_canvas.pack(fill='x')
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=STYLE["font_main"], bg=STYLE["widget_bg"], fg=STYLE["foreground"], insertbackground=STYLE["primary_neon"], relief=tk.FLAT, borderwidth=0)
        
        def on_frame_configure(e):
            search_canvas.delete("all")
            create_rounded_rect(search_canvas, 0, 0, e.width, e.height, 25, fill=STYLE["widget_bg"], outline=STYLE["secondary_neon"], width=2)
            search_entry.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.9)
        search_frame.bind("<Configure>", on_frame_configure)
        self.search_var.trace("w", self.search_apps)

        self.app_list_frame = tk.Frame(container, bg=STYLE["background"])
        self.app_list_frame.pack(pady=20, fill="both", expand=True)
        self.display_random_apps()

    def display_random_apps(self):
        for widget in self.app_list_frame.winfo_children(): widget.destroy()
        if not self.apps:
            tk.Label(self.app_list_frame, text="No apps found...", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack()
            return
        tk.Label(self.app_list_frame, text="Featured Apps", font=("Consolas", 18, "bold"), bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0,20))
        num_to_display = min(len(self.apps), 5)
        for app in random.sample(self.apps, num_to_display):
            RoundedButton(self.app_list_frame, app["name"], lambda a=app: self.show_app_details(a), width=300, height=50).pack(pady=8)
    
    def search_apps(self, *args):
        for widget in self.app_list_frame.winfo_children(): widget.destroy()
        search_term = self.search_var.get().lower()
        if not search_term: self.display_random_apps(); return
        results = [app for app in self.apps if search_term in app["name"].lower()]
        if not results:
            tk.Label(self.app_list_frame, text="No results found.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack()
        else:
            for app in results:
                RoundedButton(self.app_list_frame, app["name"], lambda a=app: self.show_app_details(a), width=300, height=50).pack(pady=8)

    def show_app_details(self, app):
        self.clear_main_frame()
        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=20, padx=20, fill="both", expand=True)

        RoundedButton(container, "< Back", self.create_home_page, width=150, height=50).pack(anchor="nw", pady=(0,20))
        tk.Label(container, text=app["name"], font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=20)
        
        button_frame = tk.Frame(container, bg=STYLE["background"])
        button_frame.pack(pady=20)
        
        is_installed = os.path.exists(os.path.join(os.getcwd(), app["name"]))
        
        self.install_button = RoundedButton(button_frame, "Install", lambda: self.install_app(app), width=150, height=50)
        self.uninstall_button = RoundedButton(button_frame, "Uninstall", lambda: self.uninstall_app(app), width=150, height=50)
        self.open_button = RoundedButton(button_frame, "Open", lambda: self.open_app(app), width=150, height=50)
        self.info_button = RoundedButton(button_frame, "Description", lambda: self.open_info_website(app), width=150, height=50)

        self.install_button.pack(side=tk.LEFT, padx=10)
        self.uninstall_button.pack(side=tk.LEFT, padx=10)
        self.open_button.pack(side=tk.LEFT, padx=10)
        self.info_button.pack(side=tk.LEFT, padx=10)
        self.update_buttons(is_installed)

        tk.Label(container, text="Click 'Description' to open app details in a new window.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["secondary_neon"], wraplength=500).pack(pady=40)

    def update_buttons(self, is_installed):
        # KORREKTUR: Alle Aufrufe von .config() zu .set_state() geändert
        if is_installed:
            self.install_button.set_state(state=tk.DISABLED)
            self.uninstall_button.set_state(state=tk.NORMAL)
            self.open_button.set_state(state=tk.NORMAL)
        else:
            self.install_button.set_state(state=tk.NORMAL)
            self.uninstall_button.set_state(state=tk.DISABLED)
            self.open_button.set_state(state=tk.DISABLED)
    
    def open_info_website(self, app):
        try:
            webview.create_window(f"Info - {app['name']}", app['website_url'], width=800, height=600)
            webview.start()
        except Exception as e:
            CustomDialog(self, "Error", f"Could not open the description window: {e}").showerror()

    def install_app(self, app):
        self.progress_label = tk.Label(self.main_frame, text="Initializing download...", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["tertiary_neon"])
        self.progress_label.pack(pady=10)
        # KORREKTUR: Aufruf zu .set_state() geändert
        self.install_button.set_state(state=tk.DISABLED)
        threading.Thread(target=self._download_and_extract, args=(app,)).start()

    def _download_and_extract(self, app):
        try:
            app_dir=os.path.join(os.getcwd(),app["name"]);os.makedirs(app_dir,exist_ok=True);zip_path=os.path.join(app_dir,"app.zip")
            with requests.get(app["download_url"],stream=True)as r:
                r.raise_for_status();total_size=int(r.headers.get('content-length',0));downloaded=0
                with open(zip_path,"wb")as f:
                    for chunk in r.iter_content(chunk_size=8192):f.write(chunk);downloaded+=len(chunk);progress=(downloaded/total_size)*100 if total_size>0 else 0;self.progress_label.config(text=f"Downloading...{downloaded/1024:.0f}KB/{total_size/1024:.0f}KB({progress:.1f}%)")
            self.progress_label.config(text="Extracting...");
            with zipfile.ZipFile(zip_path,'r')as z:z.extractall(app_dir);
            os.remove(zip_path);self.progress_label.config(text=f"'{app['name']}' installed successfully!")
            self.update_buttons(True)
            CustomDialog(self, "Success", f"{app['name']} installed successfully.").showinfo()
        except Exception as e:
            CustomDialog(self, "Error", f"An error occurred: {e}").showerror()
            # KORREKTUR: Aufruf zu .set_state() geändert
            self.install_button.set_state(state=tk.NORMAL)
        finally:
            if hasattr(self, 'progress_label'): self.after(5000, self.progress_label.destroy)

    def uninstall_app(self, app):
        dialog = CustomDialog(self, "Confirm", f"Are you sure you want to uninstall {app['name']}?")
        if dialog.askyesno():
            try:
                shutil.rmtree(os.path.join(os.getcwd(), app["name"]))
                CustomDialog(self, "Success", f"{app['name']} uninstalled successfully.").showinfo()
                self.update_buttons(False)
            except Exception as e: CustomDialog(self, "Error", f"Failed to uninstall: {e}").showerror()

    def open_app(self, app):
        app_path=os.path.join(os.getcwd(),app["name"],"main.exe")
        if os.path.exists(app_path):
            try:subprocess.Popen(app_path,cwd=os.path.dirname(app_path))
            except Exception as e:CustomDialog(self, "Error", f"Failed to open app: {e}").showerror()
        else:CustomDialog(self, "Error", "'main.exe' not found in the app directory!").showerror()

if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()