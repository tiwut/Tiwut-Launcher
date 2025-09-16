import os
import sys

# =============================================================================
# PyInstaller Workaround for Tkinter Data Files
# This block ensures that when the app is packaged as a one-file executable,
# it can find the necessary Tcl/Tk data files. It must be at the top,
# before tkinter is imported.
# =============================================================================
if hasattr(sys, '_MEIPASS'):
    # If running in a PyInstaller bundle
    os.environ['TCL_LIBRARY'] = os.path.join(sys._MEIPASS, 'tcl')
    os.environ['TK_LIBRARY'] = os.path.join(sys._MEIPASS, 'tk')
# =============================================================================

import requests
import subprocess
import tkinter as tk
from tkinter import ttk
from urllib.parse import urljoin
import ctypes

# ... der Rest Ihres Codes bleibt unverändert ...

def run_as_admin():
    """
    Ensures the script is run with administrator privileges on Windows.
    If not, it restarts itself with elevated rights.
    """
    if os.name == 'nt':  # Only relevant for Windows operating systems
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False

        if not is_admin:
            # Relaunch the script with elevated privileges
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                print(f"Error requesting admin rights: {e}")
            sys.exit()  # Exit the original, non-privileged process


class Updater:
    def __init__(self):
        self.base_url = "https://launcher.tiwut.de/Launcher/"
        self.sys_file_url = urljoin(self.base_url, "sys.tiwut")
        self.local_sys_file = "sys.tiwut"
        self.launcher_exe = "Tiwut_Launcher.exe"

        self.root = tk.Tk()
        self.root.title("Tiwut Launcher Updater")
        self.root.geometry("300x100")
        self.root.resizable(False, False)

        self.progress_label = tk.Label(self.root, text="Checking for updates...")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=280, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.root.after(100, self.check_for_updates)
        self.root.mainloop()

    def get_remote_version(self):
        try:
            response = requests.get(self.sys_file_url)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            self.update_status(f"Please check your internet connection: {e}")
            return None

    def get_local_version(self):
        if os.path.exists(self.local_sys_file):
            with open(self.local_sys_file, "r") as f:
                return f.read().strip()
        return None

    def check_for_updates(self):
        remote_version = self.get_remote_version()
        if not remote_version:
            self.launch_and_close()
            return

        local_version = self.get_local_version()

        if remote_version != local_version:
            self.update_status(f"New version {remote_version} found. Downloading...")
            self.download_update(remote_version)
        else:
            self.update_status("You have the latest version.")
            self.launch_and_close()

    def download_update(self, version):
        file_name = version
        download_url = urljoin(self.base_url, file_name)

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            self.progress_bar["maximum"] = total_size

            with open(file_name, "wb") as f:
                downloaded_amount = 0
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded_amount += len(data)
                    self.progress_bar["value"] = downloaded_amount
                    self.root.update_idletasks()
            
            with open(self.local_sys_file, "w") as f:
                f.write(version)

            self.rename_and_launch(file_name)

        except requests.RequestException as e:
            self.update_status(f"Error during download: {e}")

    def rename_and_launch(self, downloaded_file):
        try:
            if os.path.exists(self.launcher_exe):
                os.remove(self.launcher_exe)
            os.rename(downloaded_file, self.launcher_exe)
            self.launch_and_close()
        except OSError as e:
            self.update_status(f"An error occurred: {e}")

    def launch_and_close(self):
        if os.path.exists(self.launcher_exe):
            try:
                subprocess.Popen([self.launcher_exe])
            except OSError as e:
                self.update_status(f"Failed to start the launcher: {e}")
        else:
            self.update_status("Launcher not found, please reinstall.")
        
        # A short delay before closing makes the final message readable
        self.root.after(2000, self.root.destroy)


    def update_status(self, message):
        self.progress_label.config(text=message)
        self.root.update_idletasks()

if __name__ == "__main__":
    run_as_admin()  # Request admin rights before starting the app
    Updater()