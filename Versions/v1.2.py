import tkinter as tk
from tkinter import messagebox
import os
import requests
import zipfile
import subprocess
import threading
import random
import shutil
import webview  # Import der neuen Bibliothek

class TiwutLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tiwut Launcher")
        self.geometry("800x600")

        # Die URL zur Online-Bibliothek
        self.library_url = "https://launcher.tiwut.de/library.tiwut"
        self.apps = self.load_library_from_url()

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_home_page()

    def load_library_from_url(self):
        """
        Lädt die App-Bibliothek von einer URL statt aus einer lokalen Datei.
        """
        apps = []
        try:
            response = requests.get(self.library_url)
            # Wirft einen Fehler, wenn die Anfrage nicht erfolgreich war (z.B. 404 Not Found)
            response.raise_for_status()
            
            # response.text enthält den Inhalt der Online-Datei
            for line in response.text.splitlines():
                if line.strip(): # Ignoriere leere Zeilen
                    parts = line.strip().split(";")
                    if len(parts) == 3:
                        apps.append({"name": parts[0], "download_url": parts[1], "website_url": parts[2]})
        except requests.exceptions.RequestException as e:
            # Zeigt eine Fehlermeldung an, wenn die Bibliothek nicht geladen werden konnte
            messagebox.showerror("Network Error", f"Could not load the app library:\n{e}")
            # Beendet das Programm, da es ohne Bibliothek nicht funktioniert
            self.quit()
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
            no_apps_label = tk.Label(self.app_list_frame, text="No apps found in the online library.", font=("Helvetica", 16))
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
        button_frame.pack(pady=20)

        app_path = os.path.join(os.getcwd(), app["name"])
        is_installed = os.path.exists(app_path)

        self.install_button = tk.Button(button_frame, text="Install", command=lambda: self.install_app(app), width=15)
        self.uninstall_button = tk.Button(button_frame, text="Uninstall", command=lambda: self.uninstall_app(app), width=15)
        self.open_button = tk.Button(button_frame, text="Open", command=lambda: self.open_app(app), width=15)
        # Neuer Button, um die Website in einem separaten Fenster anzuzeigen
        self.info_button = tk.Button(button_frame, text="Show Description", command=lambda: self.open_info_website(app), width=15)


        self.install_button.pack(side=tk.LEFT, padx=5)
        self.uninstall_button.pack(side=tk.LEFT, padx=5)
        self.open_button.pack(side=tk.LEFT, padx=5)
        self.info_button.pack(side=tk.LEFT, padx=5)


        self.update_buttons(is_installed)

    def open_info_website(self, app):
        """
        Öffnet die Beschreibungs-Website in einem neuen, nativen Browserfenster.
        """
        try:
            webview.create_window(f"Info - {app['name']}", app['website_url'])
            webview.start()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the description window: {e}")


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
        # Zeigt den Fortschritt direkt auf dem Button an
        self.progress_label = tk.Label(self.main_frame, text="Starting download...", font=("Helvetica", 10))
        self.progress_label.pack(pady=5)
        self.install_button.config(state=tk.DISABLED)
        # Startet den Download in einem separaten Thread, um die GUI nicht zu blockieren
        threading.Thread(target=self._download_and_extract, args=(app,)).start()

    def _download_and_extract(self, app):
        try:
            app_dir = os.path.join(os.getcwd(), app["name"])
            if not os.path.exists(app_dir):
                os.makedirs(app_dir)

            zip_path = os.path.join(app_dir, "app.zip")
            
            with requests.get(app["download_url"], stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Aktualisiert den Fortschrittstext
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        self.progress_label.config(text=f"Downloading... {downloaded // 1024} KB / {total_size // 1024} KB ({progress:.1f}%)")

            self.progress_label.config(text="Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(app_dir)

            os.remove(zip_path)
            
            self.progress_label.config(text=f"'{app['name']}' installed successfully!")
            messagebox.showinfo("Success", f"{app['name']} installed successfully.")
            self.update_buttons(True)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to download: {e}")
            self.install_button.config(state=tk.NORMAL)
        except zipfile.BadZipFile:
            messagebox.showerror("Error", "Failed to extract. The downloaded file is not a valid zip file.")
            self.install_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            self.install_button.config(state=tk.NORMAL)
        finally:
            # Nach 5 Sekunden den Fortschrittstext ausblenden
            self.after(5000, self.progress_label.destroy)


    def uninstall_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"])
        if messagebox.askyesno("Confirm", f"Are you sure you want to uninstall {app['name']}?"):
            try:
                shutil.rmtree(app_path)
                messagebox.showinfo("Success", f"{app['name']} uninstalled successfully.")
                self.update_buttons(False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to uninstall: {e}")

    def open_app(self, app):
        app_path = os.path.join(os.getcwd(), app["name"], "main.exe")
        if os.path.exists(app_path):
            try:
                # Starte die App in ihrem eigenen Verzeichnis, damit sie ihre Dateien findet
                subprocess.Popen(app_path, cwd=os.path.dirname(app_path))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open app: {e}")
        else:
            messagebox.showerror("Error", "'main.exe' not found in the app directory!")


if __name__ == "__main__":
    app = TiwutLauncher()
    app.mainloop()