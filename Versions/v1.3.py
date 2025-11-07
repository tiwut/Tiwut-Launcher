import tkinter as tk
from tkinter import messagebox, font
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
    "background": "#1a1a1a",
    "foreground": "#e0e0e0",
    "primary_neon": "#ff00ff",   # Leuchtendes Pink
    "secondary_neon": "#00ffff", # Cyan / Türkis
    "tertiary_neon": "#fcee0c",    # Neongelb
    "widget_bg": "#2a2a2a",
    "font_main": ("Consolas", 12),
    "font_title": ("Consolas", 28, "bold"),
    "font_button": ("Consolas", 14, "bold"),
}

# --- Ein benutzerdefinierter Button mit Neon-Hover-Effekt ---
class NeonButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=STYLE["font_button"],
            bg=STYLE["widget_bg"],
            fg=STYLE["primary_neon"],
            activebackground=STYLE["primary_neon"],
            activeforeground=STYLE["widget_bg"],
            relief=tk.FLAT,
            borderwidth=2,
            pady=5,
            padx=10
        )
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

    def on_hover(self, event):
        self.config(bg=STYLE["primary_neon"], fg=STYLE["widget_bg"])

    def on_leave(self, event):
        self.config(bg=STYLE["widget_bg"], fg=STYLE["primary_neon"])

# --- Partikel-Klasse für die Hintergrundanimation ---
class Particle:
    def __init__(self, canvas):
        self.canvas = canvas
        self.id = None
        self.reset()

    def reset(self):
        if self.id:
            self.canvas.delete(self.id)
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.color = random.choice([STYLE["primary_neon"], STYLE["secondary_neon"], STYLE["tertiary_neon"]])
        self.id = self.canvas.create_line(self.x, self.y, self.x+self.vx*2, self.y+self.vy*2, fill=self.color, width=2)

    def move(self):
        self.x += self.vx
        self.y += self.vy
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if not (0 < self.x < width and 0 < self.y < height):
            self.reset()
        else:
            self.canvas.coords(self.id, self.x, self.y, self.x+self.vx*5, self.y+self.vy*5)


# --- Hauptklasse des Launchers ---
class TiwutLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut Launcher")
        self.geometry("900x700")
        self.configure(bg=STYLE["background"])
        
        # Für den Fade-In-Effekt
        self.attributes("-alpha", 0)

        # Hintergrund-Canvas für Animation
        self.canvas = tk.Canvas(self, bg=STYLE["background"], highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Haupt-Frame für den Inhalt
        self.main_frame = tk.Frame(self, bg=STYLE["background"])
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.library_url = "https://launcher.tiwut.de/library.tiwut"
        self.apps = self.load_library_from_url()

        self.create_home_page()
        
        self.after(100, self.init_animation)
        self.after(500, self.fade_in)

    def fade_in(self, alpha=0):
        if alpha < 1:
            alpha += 0.05
            self.attributes("-alpha", alpha)
            self.after(25, lambda: self.fade_in(alpha))

    def init_animation(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width > 1 and canvas_height > 1:
            self.particles = [Particle(self.canvas) for _ in range(50)]
            self.update_animation()
        else:
            self.after(100, self.init_animation)

    def update_animation(self):
        for p in self.particles:
            p.move()
        self.after(33, self.update_animation) # ca. 30 FPS

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            # Canvas nicht löschen!
            if widget != self.canvas:
                widget.destroy()

    def load_library_from_url(self):
        # Diese Funktion bleibt logisch unverändert
        apps = []
        try:
            response = requests.get(self.library_url)
            response.raise_for_status()
            for line in response.text.splitlines():
                if line.strip():
                    parts = line.strip().split(";")
                    if len(parts) == 3:
                        apps.append({"name": parts[0], "download_url": parts[1], "website_url": parts[2]})
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not load the app library:\n{e}")
            self.quit()
        return apps

    def create_home_page(self):
        self.clear_main_frame()

        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=40, padx=20, fill="both", expand=True)

        title = tk.Label(container, text="T I W U T", font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"])
        title.pack(pady=(0, 40))

        # Suchleiste
        search_frame = tk.Frame(container, bg=STYLE["background"])
        search_frame.pack(pady=20, fill='x', padx=50)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=STYLE["font_main"], bg=STYLE["widget_bg"], fg=STYLE["foreground"], insertbackground=STYLE["primary_neon"], relief=tk.FLAT, borderwidth=2)
        search_entry.pack(fill='x', expand=True)
        self.search_var.trace("w", self.search_apps)

        self.app_list_frame = tk.Frame(container, bg=STYLE["background"])
        self.app_list_frame.pack(pady=20, fill="both", expand=True)

        self.display_random_apps()

    def display_random_apps(self):
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()

        if not self.apps:
            tk.Label(self.app_list_frame, text="No apps found in the online library.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack(pady=20)
            return

        tk.Label(self.app_list_frame, text="Featured Apps", font=("Consolas", 18, "bold"), bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0,20))

        num_to_display = min(len(self.apps), 5)
        random_apps = random.sample(self.apps, num_to_display)

        for app in random_apps:
            NeonButton(self.app_list_frame, text=app["name"], command=lambda a=app: self.show_app_details(a)).pack(pady=8)

    def search_apps(self, *args):
        # Logik bleibt gleich, nur das Aussehen wird angepasst
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()

        search_term = self.search_var.get().lower()
        if not search_term:
            self.display_random_apps()
            return
        
        results = [app for app in self.apps if search_term in app["name"].lower()]

        if not results:
            tk.Label(self.app_list_frame, text="No results found.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack(pady=20)
        else:
            for app in results:
                NeonButton(self.app_list_frame, text=app["name"], command=lambda a=app: self.show_app_details(a)).pack(pady=8)

    def show_app_details(self, app):
        self.clear_main_frame()
        
        container = tk.Frame(self.main_frame, bg=STYLE["background"])
        container.pack(pady=20, padx=20, fill="both", expand=True)

        NeonButton(container, text="< Back", command=self.create_home_page).pack(anchor="nw", pady=(0,20))

        tk.Label(container, text=app["name"], font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=20)
        
        button_frame = tk.Frame(container, bg=STYLE["background"])
        button_frame.pack(pady=20)
        
        app_path = os.path.join(os.getcwd(), app["name"])
        is_installed = os.path.exists(app_path)
        
        self.install_button = NeonButton(button_frame, text="Install", command=lambda: self.install_app(app))
        self.uninstall_button = NeonButton(button_frame, text="Uninstall", command=lambda: self.uninstall_app(app))
        self.open_button = NeonButton(button_frame, text="Open", command=lambda: self.open_app(app))
        self.info_button = NeonButton(button_frame, text="Description", command=lambda: self.open_info_website(app))

        self.install_button.pack(side=tk.LEFT, padx=10)
        self.uninstall_button.pack(side=tk.LEFT, padx=10)
        self.open_button.pack(side=tk.LEFT, padx=10)
        self.info_button.pack(side=tk.LEFT, padx=10)
        
        self.update_buttons(is_installed)

        # Ein Platzhalter, wo die Webseite angezeigt *würde*, wenn sie integriert wäre.
        # Da wir sie in einem neuen Fenster öffnen, zeigen wir stattdessen eine Info.
        info_label = tk.Label(container, text="Click 'Description' to open app details in a new window.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["secondary_neon"], wraplength=500)
        info_label.pack(pady=40)

    def update_buttons(self, is_installed):
        if is_installed:
            self.install_button.config(state=tk.DISABLED, bg=STYLE["widget_bg"], fg="#555")
            self.uninstall_button.config(state=tk.NORMAL)
            self.open_button.config(state=tk.NORMAL)
        else:
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.DISABLED, bg=STYLE["widget_bg"], fg="#555")
            self.open_button.config(state=tk.DISABLED, bg=STYLE["widget_bg"], fg="#555")
    
    # --- Kernfunktionen (Install, Uninstall, etc.) bleiben unverändert in ihrer Logik ---
    def open_info_website(self, app):
        try:
            webview.create_window(f"Info - {app['name']}", app['website_url'], width=800, height=600)
            webview.start()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the description window: {e}")

    def install_app(self, app):
        self.progress_label = tk.Label(self.main_frame, text="Initializing download...", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["tertiary_neon"])
        self.progress_label.pack(pady=10)
        self.install_button.config(state=tk.DISABLED, bg=STYLE["widget_bg"], fg="#555")
        threading.Thread(target=self._download_and_extract, args=(app,)).start()

    def _download_and_extract(self, app):
        try:
            app_dir = os.path.join(os.getcwd(), app["name"])
            if not os.path.exists(app_dir): os.makedirs(app_dir)
            zip_path = os.path.join(app_dir, "app.zip")
            with requests.get(app["download_url"], stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        self.progress_label.config(text=f"Downloading... {downloaded / 1024:.0f} KB / {total_size / 1024:.0f} KB ({progress:.1f}%)")
            self.progress_label.config(text="Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(app_dir)
            os.remove(zip_path)
            self.progress_label.config(text=f"'{app['name']}' installed successfully!")
            messagebox.showinfo("Success", f"{app['name']} installed successfully.")
            self.update_buttons(True)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.install_button.config(state=tk.NORMAL)
        finally:
            self.after(5000, self.progress_label.destroy)

    def uninstall_app(self, app):
        if messagebox.askyesno("Confirm", f"Are you sure you want to uninstall {app['name']}?"):
            try:
                shutil.rmtree(os.path.join(os.getcwd(), app["name"]))
                messagebox.showinfo("Success", f"{app['name']} uninstalled successfully.")
                self.update_buttons(False)
            except Exception as e: messagebox.showerror("Error", f"Failed to uninstall: {e}")

    def open_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"], "main.exe")
        if os.path.exists(app_path):
            try:
                subprocess.Popen(app_path, cwd=os.path.dirname(app_path))
            except Exception as e: messagebox.showerror("Error", f"Failed to open app: {e}")
        else:
            messagebox.showerror("Error", "'main.exe' not found in the app directory!")


if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()