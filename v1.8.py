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
    "background": "#000000", "transparent_color": "lime green", "foreground": "#e0e0e0",
    "primary_neon": "#ff00ff", "secondary_neon": "#00ffff", "tertiary_neon": "#fcee0c",
    "widget_bg": "#1a1a1a", "disabled_fg": "#555555",
    "font_main": ("Consolas", 12), "font_title": ("Consolas", 18, "bold"), "font_button": ("Consolas", 14, "bold"),
    "font_nav": ("Consolas", 16, "bold")
}

# --- Helper für gerundete Rechtecke ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1+radius,y1, x1+radius,y1, x2-radius,y1, x2-radius,y1, x2,y1, x2,y1+radius, x2,y1+radius, x2,y2-radius, x2,y2-radius, x2,y2, x2-radius,y2, x2-radius,y2, x1+radius,y2, x1+radius,y2, x1,y2, x1,y2-radius, x1,y2-radius, x1,y1+radius, x1,y1+radius, x1,y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- Scrollbare Frame-Klasse (optimiert für Zentrierung) ---
class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.config(bg=STYLE["background"])
        self.canvas = tk.Canvas(self, bg=STYLE["background"], highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=STYLE["background"])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bind('<Enter>', self._bind_to_mousewheel)
        self.bind('<Leave>', self._unbind_from_mousewheel)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _bind_to_mousewheel(self, event): self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    def _unbind_from_mousewheel(self, event): self.canvas.unbind_all("<MouseWheel>")
    def _on_mousewheel(self, event): self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class AnimatedProgressBar(tk.Frame):
    def __init__(self, master, height=40):
        super().__init__(master, bg=STYLE["background"]); self.canvas = tk.Canvas(self, height=height, bg=STYLE["background"], highlightthickness=0); self.canvas.pack(fill='x', expand=True, padx=50, pady=(20, 10)); self.status_text_id = self.canvas.create_text(0, 0, text="Initializing...", font=("Consolas", 12), fill=STYLE["secondary_neon"]); self.info_text_id = self.canvas.create_text(0, 0, text="", font=("Consolas", 10), fill=STYLE["tertiary_neon"]); self.canvas.bind("<Configure>", self._on_resize); self.current_percentage = 0; self.target_percentage = 0; self._target_status = "Initializing..."; self._target_info = ""; self._animate_progress()
    def _on_resize(self, e=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height();
        if w < 10: return;
        self.canvas.delete("all"); create_rounded_rect(self.canvas, 2, h - 22, w - 2, h - 2, radius=10, fill=STYLE["widget_bg"], width=0); self.progress_rect = create_rounded_rect(self.canvas, 2, h - 22, 2, h - 2, radius=10, fill=STYLE["tertiary_neon"], width=0); self.status_text_id = self.canvas.create_text(w / 2, 10, text=self._target_status, font=("Consolas", 12), fill=STYLE["secondary_neon"]); self.info_text_id = self.canvas.create_text(w / 2, h - 12, text=self._target_info, font=("Consolas", 10), fill=STYLE["tertiary_neon"])
    def update_full(self, p, s, i): self.target_percentage, self._target_status, self._target_info = p, s, i
    def _animate_progress(self):
        if abs(self.target_percentage - self.current_percentage) > 0.1: self.current_percentage += (self.target_percentage - self.current_percentage) * 0.2
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 10: new_width = (w - 4) * (self.current_percentage / 100); self.canvas.coords(self.progress_rect, 2, h - 22, max(2, new_width), h - 2); self.canvas.itemconfig(self.status_text_id, text=self._target_status); self.canvas.itemconfig(self.info_text_id, text=self._target_info)
        self.after(20, self._animate_progress)

def format_bytes(size):
    power=1024;n=0;labels={0:'',1:'K',2:'M',3:'G',4:'T'};
    while size>=power and n<len(labels)-1:size/=power;n+=1
    return f"{size:.1f} {labels[n]}B"

class RoundedButton(tk.Frame):
    def __init__(self, master, text, command, width, height, radius=25, font=STYLE["font_button"]):
        super().__init__(master, width=width, height=height, bg=STYLE["background"]); self.command = command; self.is_disabled = False; self.is_active = False; self.canvas = tk.Canvas(self, width=width, height=height, bg=STYLE["background"], highlightthickness=0); self.canvas.pack(); self.shape = create_rounded_rect(self.canvas, 0, 0, width, height, radius, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"], width=2); self.text_label = self.canvas.create_text(width/2, height/2, text=text, font=font, fill=STYLE["primary_neon"]); self.canvas.bind("<Button-1>", self._on_click); self.canvas.bind("<Enter>", self._on_hover); self.canvas.bind("<Leave>", self._on_leave)
    def _on_click(self, e):
        if self.command and not self.is_disabled: self.command()
    def _on_hover(self, e):
        if not self.is_disabled and not self.is_active: self.canvas.itemconfig(self.shape, fill=STYLE["primary_neon"]); self.canvas.itemconfig(self.text_label, fill=STYLE["widget_bg"])
    def _on_leave(self, e):
        if not self.is_disabled and not self.is_active: self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"]); self.canvas.itemconfig(self.text_label, fill=STYLE["primary_neon"])
    def set_state(self, state=None):
        self.is_disabled, self.is_active = False, False
        if state == tk.DISABLED: self.is_disabled = True; self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["disabled_fg"]); self.canvas.itemconfig(self.text_label, fill=STYLE["disabled_fg"])
        elif state == "active": self.is_active = True; self.canvas.itemconfig(self.shape, fill=STYLE["secondary_neon"], outline=STYLE["secondary_neon"]); self.canvas.itemconfig(self.text_label, fill=STYLE["widget_bg"])
        else: self.canvas.itemconfig(self.shape, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"]); self.canvas.itemconfig(self.text_label, fill=STYLE["primary_neon"])

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
        super().__init__(); self.overrideredirect(True); self.geometry("1100x700"); self.attributes("-transparentcolor",STYLE["transparent_color"]); self.config(bg=STYLE["transparent_color"]); self.bg_canvas = tk.Canvas(self, bg=STYLE["transparent_color"], highlightthickness=0); self.bg_canvas.pack(fill="both", expand=True); self.bind("<Configure>", self.draw_background); self.content_frame = tk.Frame(self, bg=STYLE["background"]); self.bg_canvas.create_window(0, 0, anchor="nw", window=self.content_frame); self.title_bar = tk.Frame(self.content_frame, bg=STYLE["widget_bg"], bd=0); self.title_bar.pack(expand=0, fill='x'); tk.Label(self.title_bar, text="Tiwut Launcher", bg=STYLE["widget_bg"], fg=STYLE["secondary_neon"], font=("Consolas", 10)).pack(side='left', padx=10); tk.Button(self.title_bar, text='X', command=self.destroy, bg=STYLE["widget_bg"], fg=STYLE["primary_neon"], relief="flat", font=("Consolas", 10, "bold")).pack(side='right', padx=5); self.title_bar.bind("<ButtonPress-1>", self.start_move); self.title_bar.bind("<ButtonRelease-1>", self.stop_move); self.title_bar.bind("<B1-Motion>", self.on_motion); self.main_frame = tk.Frame(self.content_frame, bg=STYLE["background"]); self.main_frame.pack(fill=tk.BOTH, expand=True); self.library_url = "https://launcher.tiwut.de/library.tiwut"; self.apps = self.load_library_from_url(); self.create_home_page()
    def draw_background(self, event=None): self.bg_canvas.delete("all"); w, h = self.winfo_width(), self.winfo_height(); create_rounded_rect(self.bg_canvas, 0, 0, w, h, 30, fill=STYLE["background"]); self.bg_canvas.create_window(0, 0, anchor="nw", window=self.content_frame, width=w, height=h)
    def start_move(self, e): self.x, self.y = e.x, e.y
    def stop_move(self, e): self.x, self.y = None, None
    def on_motion(self, e): self.geometry(f"+{self.winfo_x() + (e.x - self.x)}+{self.winfo_y() + (e.y - self.y)}")
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
    def load_library_from_url(self):
        apps = [];
        try:
            r = requests.get(self.library_url); r.raise_for_status()
            for line in r.text.splitlines():
                if line.strip(): p = line.strip().split(";");
                if len(p) == 3: apps.append({"name": p[0], "download_url": p[1], "website_url": p[2]})
        except requests.exceptions.RequestException as e: CustomDialog(self, "Network Error", f"Could not load library:\n{e}").showerror(); self.quit()
        return apps

    def _create_navigation(self, active_page):
        nav_frame = tk.Frame(self.main_frame, bg=STYLE["background"]); nav_frame.pack(pady=20)
        self.home_button = RoundedButton(nav_frame, "My Apps", self.create_home_page, 200, 50, font=STYLE["font_nav"]); self.home_button.pack(side="left", padx=10)
        self.discover_button = RoundedButton(nav_frame, "Discover", self.create_discover_page, 200, 50, font=STYLE["font_nav"]); self.discover_button.pack(side="left", padx=10)
        if active_page == "home": self.home_button.set_state("active")
        elif active_page == "discover": self.discover_button.set_state("active")

    def create_home_page(self):
        self.clear_main_frame(); self._create_navigation("home")
        tk.Label(self.main_frame, text="My Installed Apps", font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0, 10))
        self.s_var = tk.StringVar(); self.s_var.trace("w", self._search_installed)
        self._create_search_bar(self.s_var)
        self.installed_list_frame = ScrollableFrame(self.main_frame); self.installed_list_frame.pack(pady=10, fill="both", expand=True, padx=50)
        self._populate_installed_list()

    def create_discover_page(self):
        self.clear_main_frame(); self._create_navigation("discover")
        tk.Label(self.main_frame, text="Discover New Apps", font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0, 10))
        self.discover_s_var = tk.StringVar(); self.discover_s_var.trace("w", self._search_discover)
        self._create_search_bar(self.discover_s_var)
        self.app_list_frame = ScrollableFrame(self.main_frame); self.app_list_frame.pack(pady=10, fill="both", expand=True, padx=50)
        self._populate_discover_list(random.sample(self.apps, min(len(self.apps), 15)), "Featured Apps")

    def _create_search_bar(self, var):
        sc = tk.Frame(self.main_frame, bg=STYLE["background"]); sc.pack(pady=10, fill='x', padx=200); s_cv = tk.Canvas(sc, height=50, bg=STYLE["background"], highlightthickness=0); s_cv.pack(fill='x'); s_entry = tk.Entry(sc, textvariable=var, font=STYLE["font_main"], bg=STYLE["widget_bg"], fg=STYLE["foreground"], insertbackground=STYLE["primary_neon"], relief=tk.FLAT, bd=0); ph = "Type to search..."; s_entry.insert(0, ph); s_entry.config(fg='grey')
        def on_fin(e):
            if s_entry.get() == ph: s_entry.delete(0, "end"); s_entry.config(fg=STYLE["foreground"])
        def on_fout(e):
            if not s_entry.get(): s_entry.insert(0, ph); s_entry.config(fg='grey')
        s_entry.bind("<FocusIn>", on_fin); s_entry.bind("<FocusOut>", on_fout)
        def on_frame_conf(e): s_cv.delete("all"); create_rounded_rect(s_cv, 0, 0, e.width, e.height, 25, fill=STYLE["widget_bg"], outline=STYLE["primary_neon"], width=2); s_entry.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.9)
        sc.bind("<Configure>", on_frame_conf)
    
    def _search_installed(self, *args):
        search_term = self.s_var.get().lower()
        if not search_term or search_term == "type to search...": self._populate_installed_list(); return
        results = [app for app in self._get_installed_apps() if search_term in app["name"].lower()]; self._populate_installed_list(results, "Search Results")
    def _search_discover(self, *args):
        search_term = self.discover_s_var.get().lower()
        if not search_term or search_term == "type to search...": self._populate_discover_list(random.sample(self.apps, min(len(self.apps), 15)), "Featured Apps"); return
        results = [app for app in self.apps if search_term in app["name"].lower()]; self._populate_discover_list(results, "Search Results")

    def _populate_discover_list(self, apps_to_show, title):
        frame = self.app_list_frame.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        tk.Label(frame, text=title, font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0, 20))
        if not apps_to_show: tk.Label(frame, text="No results found.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack(); return
        center_frame = tk.Frame(frame, bg=STYLE["background"]); center_frame.pack(expand=True)
        for app in apps_to_show: RoundedButton(center_frame, app["name"], lambda a=app: self.show_app_details(a), 600, 50).pack(pady=8)
    
    def _get_installed_apps(self): return [app for app in self.apps if os.path.exists(os.path.join(os.getcwd(), app["name"]))]
    
    def _populate_installed_list(self, apps_to_show=None, title=None):
        frame = self.installed_list_frame.scrollable_frame
        for w in frame.winfo_children(): w.destroy()
        if title: tk.Label(frame, text=title, font=STYLE["font_title"], bg=STYLE["background"], fg=STYLE["secondary_neon"]).pack(pady=(0, 20))
        installed_apps = apps_to_show if apps_to_show is not None else self._get_installed_apps()
        if not installed_apps: tk.Label(frame, text="No apps found." if apps_to_show is not None else "No apps installed yet.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["foreground"]).pack(); return
        center_frame = tk.Frame(frame, bg=STYLE["background"]); center_frame.pack(expand=True)
        for app in installed_apps: RoundedButton(center_frame, app["name"], lambda a=app: self.show_app_details(a), 600, 50).pack(pady=8)
    
    def show_app_details(self, app):
        self.clear_main_frame(); cont = tk.Frame(self.main_frame, bg=STYLE["background"]); cont.pack(pady=20, padx=20, fill="both", expand=True); RoundedButton(cont, "< Back to Discover", self.create_discover_page, 250, 50).pack(anchor="nw", pady=(0, 20)); tk.Label(cont, text=app["name"], font=("Consolas", 36, "bold"), bg=STYLE["background"], fg=STYLE["primary_neon"]).pack(pady=20); bf = tk.Frame(cont, bg=STYLE["background"]); bf.pack(pady=20); is_inst = os.path.exists(os.path.join(os.getcwd(), app["name"])); self.install_b = RoundedButton(bf, "Install", lambda: self.install_app(app), 150, 50); self.uninstall_b = RoundedButton(bf, "Uninstall", lambda: self.uninstall_app(app), 150, 50); self.open_b = RoundedButton(bf, "Open", lambda: self.open_app(app), 150, 50); self.info_b = RoundedButton(bf, "View Details", lambda: self.open_info_website(app), 150, 50); self.install_b.pack(side=tk.LEFT, padx=10); self.uninstall_b.pack(side=tk.LEFT, padx=10); self.open_b.pack(side=tk.LEFT, padx=10); self.info_b.pack(side=tk.LEFT, padx=10); self.update_buttons(is_inst); tk.Label(cont, text="Click 'View Details' to open app info in a new window.", font=STYLE["font_main"], bg=STYLE["background"], fg=STYLE["secondary_neon"], wraplength=500).pack(pady=40)
    
    def update_buttons(self, is_inst):
        if is_inst: self.install_b.set_state(tk.DISABLED); self.uninstall_b.set_state(tk.NORMAL); self.open_b.set_state(tk.NORMAL)
        else: self.install_b.set_state(tk.NORMAL); self.uninstall_b.set_state(tk.DISABLED); self.open_b.set_state(tk.DISABLED)
    
    def open_info_website(self, app):
        try: webview.create_window(f"Details - {app['name']}", app['website_url'], width=800, height=600); webview.start()
        except Exception as e: CustomDialog(self, "Error", f"Could not open window:\n{e}").showerror()
    
    def install_app(self, app):
        self.progress_bar = AnimatedProgressBar(self.main_frame); self.progress_bar.pack(fill='x', side='bottom'); self.install_b.set_state(tk.DISABLED); threading.Thread(target=self._download_and_extract, args=(app,)).start()
    
    def _download_and_extract(self, app):
        try:
            self.after(0, self.progress_bar.update_full, 0, "Connecting...", "Waiting for server response"); app_dir = os.path.join(os.getcwd(), app["name"]); os.makedirs(app_dir, exist_ok=True); zip_path = os.path.join(app_dir, "app.zip")
            with requests.get(app["download_url"], stream=True) as r:
                r.raise_for_status(); total_size = int(r.headers.get('content-length', 0)); downloaded = 0; last_upd_t = time.time(); dl_since_upd = 0
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk); downloaded += len(chunk); dl_since_upd += len(chunk)
                        curr_t = time.time()
                        if total_size > 0 and (curr_t - last_upd_t) > 0.2:
                            prog = (downloaded / total_size) * 100; el_t = curr_t - last_upd_t; speed = dl_since_upd / el_t if el_t > 0 else 0; status = "Downloading App..."; info = f"{format_bytes(speed)}/s  |  {format_bytes(downloaded)} / {format_bytes(total_size)}"; self.after(0, self.progress_bar.update_full, prog, status, info); last_upd_t = curr_t; dl_since_upd = 0
            self.after(0, self.progress_bar.update_full, 100, "Extracting Files...", "Unpacking, please wait..."); time.sleep(0.5)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(app_dir)
            os.remove(zip_path); self.after(0, self.progress_bar.update_full, 100, "Installation Complete", ""); time.sleep(1); self.update_buttons(True); CustomDialog(self, "Success", f"{app['name']} was installed successfully.").showinfo()
        except Exception as e: CustomDialog(self, "Error", f"An error occurred:\n{e}").showerror(); self.install_b.set_state(tk.NORMAL)
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
        else: CustomDialog(self, "Error", "'main.exe' not found!").showerror()

if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()