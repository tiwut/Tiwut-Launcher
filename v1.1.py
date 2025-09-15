import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import requests
import zipfile
import subprocess
import threading
import random
import io
from PIL import Image, ImageTk
import re

class TiwutLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut Launcher")
        self.geometry("800x600")

        self.library_file = "library.tiwut"
        self.apps = self.load_library()

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_home_page()

    def load_library(self):
        apps = []
        if os.path.exists(self.library_file):
            with open(self.library_file, "r") as f:
                for line in f:
                    parts = line.strip().split(";")
                    if len(parts) == 3:
                        apps.append({"name": parts[0], "download_url": parts[1], "website_url": parts[2]})
        return apps

    def create_home_page(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        search_frame = tk.Frame(self.main_frame)
        search_frame.pack(pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.search_apps)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_button = tk.Button(search_frame, text="Search", command=self.search_apps)
        search_button.pack(side=tk.LEFT)

        self.app_list_frame = tk.Frame(self.main_frame)
        self.app_list_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.display_random_apps()

    def display_random_apps(self):
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()

        if not self.apps:
            no_apps_label = tk.Label(self.app_list_frame, text="No apps found in library.tiwut", font=("Helvetica", 16))
            no_apps_label.pack(pady=20)
            return

        num_to_display = min(len(self.apps), 5)
        random_apps = random.sample(self.apps, num_to_display)

        for app in random_apps:
            app_button = tk.Button(self.app_list_frame, text=app["name"], command=lambda a=app: self.show_app_details(a))
            app_button.pack(pady=5)

    def search_apps(self, *args):
        search_term = self.search_var.get().lower()
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()

        if not search_term:
            self.display_random_apps()
            return

        results = [app for app in self.apps if search_term in app["name"].lower()]

        if not results:
            no_results_label = tk.Label(self.app_list_frame, text="No apps found.", font=("Helvetica", 12))
            no_results_label.pack(pady=20)
        else:
            for app in results:
                app_button = tk.Button(self.app_list_frame, text=app["name"], command=lambda a=app: self.show_app_details(a))
                app_button.pack(pady=5)

    def show_app_details(self, app):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        back_button = tk.Button(self.main_frame, text="< Back", command=self.create_home_page)
        back_button.pack(anchor="w", padx=10, pady=10)

        app_name_label = tk.Label(self.main_frame, text=app["name"], font=("Helvetica", 24, "bold"))
        app_name_label.pack(pady=10)

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=10)

        app_path = os.path.join(os.getcwd(), app["name"])
        is_installed = os.path.exists(app_path)

        self.install_button = tk.Button(button_frame, text="Install", command=lambda: self.install_app(app))
        self.uninstall_button = tk.Button(button_frame, text="Uninstall", command=lambda: self.uninstall_app(app))
        self.open_button = tk.Button(button_frame, text="Open", command=lambda: self.open_app(app))

        self.install_button.pack(side=tk.LEFT, padx=5)
        self.uninstall_button.pack(side=tk.LEFT, padx=5)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.update_buttons(is_installed)

        info_frame = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, width=80, height=20)
        info_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.load_website_info(app["website_url"], info_frame)

    def update_buttons(self, is_installed):
        if is_installed:
            self.install_button.config(state=tk.DISABLED)
            self.uninstall_button.config(state=tk.NORMAL)
            self.open_button.config(state=tk.NORMAL)
        else:
            self.install_button.config(state=tk.NORMAL)
            self.uninstall_button.config(state=tk.DISABLED)
            self.open_button.config(state=tk.DISABLED)

    def install_app(self, app):
        self.install_button.config(text="Downloading...", state=tk.DISABLED)
        threading.Thread(target=self._download_and_extract, args=(app,)).start()

    def _download_and_extract(self, app):
        try:
            response = requests.get(app["download_url"], stream=True)
            response.raise_for_status()

            app_dir = os.path.join(os.getcwd(), app["name"])
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)

            zip_path = os.path.join(app_dir, "app.zip")
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.install_button.config(text="Extracting...")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(app_dir)

            os.remove(zip_path)

            messagebox.showinfo("Success", f"{app['name']} installed successfully.")
            self.install_button.config(text="Install")
            self.update_buttons(True)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to download: {e}")
            self.install_button.config(text="Install", state=tk.NORMAL)
        except zipfile.BadZipFile:
            messagebox.showerror("Error", "Failed to extract. The downloaded file is not a valid zip file.")
            self.install_button.config(text="Install", state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.install_button.config(text="Install", state=tk.NORMAL)


    def uninstall_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"])
        if messagebox.askyesno("Confirm", f"Are you sure you want to uninstall {app['name']}?"):
            try:
                import shutil
                shutil.rmtree(app_path)
                messagebox.showinfo("Success", f"{app['name']} uninstalled successfully.")
                self.update_buttons(False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to uninstall: {e}")

    def open_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"], "main.exe")
        if os.path.exists(app_path):
            try:
                subprocess.Popen(app_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open app: {e}")
        else:
            messagebox.showerror("Error", "main.exe not found!")

    def load_website_info(self, url, text_widget):
        text_widget.insert(tk.END, "Loading...")
        def _fetch():
            try:
                response = requests.get(url)
                response.raise_for_status()
                # Simple way to clean up HTML for display
                clean_text = re.sub('<[^<]+?>', '', response.text)
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, clean_text)
            except requests.exceptions.RequestException as e:
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, f"Failed to load website info: {e}")
        threading.Thread(target=_fetch).start()


if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()