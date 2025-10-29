import os
import urllib.request
import hashlib
import tkinter as tk
from tkinter import ttk
import sys
import subprocess
import ssl
import shutil

# --- WICHTIGSTE ÄNDERUNG: ABSOLUTE PFADE ERMITTELN ---
# Ermittelt den absoluten Pfad des Verzeichnisses, in dem sich dieses Skript befindet.
# Das macht das Skript standortunabhängig und löst alle Pfadprobleme.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Konfiguration (verwendet jetzt absolute Pfade) ---
SYS_TIWUT_URL = "http://launcher.tiwut.de/Linux/sys.tiwut"
MAIN_PY_URL = "http://launcher.tiwut.de/Linux/Launcher/main.py"
COMMANDS_URL = "http://launcher.tiwut.de/Linux/Updater/sys_modul.tiwut"

# Erstellt absolute Pfade für alle lokalen Dateien und Ordner
LOCAL_SYS_TIWUT = os.path.join(SCRIPT_DIR, "sys.tiwut")
LAUNCHER_DIR = os.path.join(SCRIPT_DIR, "Launcher")
MAIN_PY_PATH = os.path.join(LAUNCHER_DIR, "main.py")
COMMANDS_FILE_PATH = os.path.join(SCRIPT_DIR, "sys_modul.tiwut")

# --- SSL Context ---
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    pass

# --- Funktionen (unverändert, aber arbeiten jetzt mit absoluten Pfaden) ---

def show_info_window(message, duration_ms=4000):
    root = tk.Tk()
    root.title("Process Info")
    root.geometry("550x170")
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    label = ttk.Label(root, text=message, wraplength=530, justify='center')
    label.pack(pady=20, padx=20, expand=True)
    root.after(duration_ms, root.destroy)
    root.mainloop()

def get_online_hash(url):
    try:
        with urllib.request.urlopen(url, context=ssl_context) as response:
            if response.status == 200:
                return hashlib.sha256(response.read()).hexdigest()
    except Exception as e:
        raise ConnectionError(f"Could not fetch hash from {url}: {e}")

def get_local_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def download_file(url, local_path):
    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, context=ssl_context) as response:
            if response.status != 200:
                raise ConnectionError(f"Server returned status {response.status}")
            data = response.read()
    except Exception as e:
        raise ConnectionError(f"Network error while downloading {url}: {e}")

    try:
        # Diese Zeile funktioniert jetzt zuverlässig, da local_path absolut ist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as out_file:
            out_file.write(data)
    except Exception as e:
        raise IOError(f"Filesystem error while saving to {local_path}: {e}")

    print(f"Successfully downloaded {local_path} from {url}")

def make_executable(filepath):
    try:
        os.chmod(filepath, 0o755)
        print(f"Made {filepath} executable.")
    except Exception as e:
        raise OSError(f"Could not make {filepath} executable: {e}")

def execute_setup_commands_in_new_terminal():
    print("Downloading setup commands file...")
    download_file(COMMANDS_URL, COMMANDS_FILE_PATH)

    try:
        with open(COMMANDS_FILE_PATH, "r") as f:
            commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        if not commands:
            print("No setup commands to execute.")
            return

        full_command_string = "sudo apt-get update && " + " && ".join(commands)
        shell_script = (
            f'echo "--- Automated Application Setup ---";'
            f'echo "System packages need to be installed or updated.";'
            f'echo "Please enter your password when prompted."; echo;'
            f'echo "Executing command: {full_command_string}"; echo;'
            f'{full_command_string};'
            f'echo; echo "--- Setup Finished ---";'
            f'read -p "Press ENTER to close this terminal.";'
        )

        terminals = [
            ('gnome-terminal', '--', '/bin/bash', '-c', shell_script),
            ('konsole', '-e', '/bin/bash', '-c', shell_script),
            ('xfce4-terminal', '-e', shell_script),
            ('xterm', '-e', shell_script)
        ]

        terminal_found = False
        for term_cmd in terminals:
            if shutil.which(term_cmd[0]):
                print(f"Opening '{term_cmd[0]}' for setup...")
                subprocess.Popen(term_cmd)
                terminal_found = True
                break
        
        if not terminal_found:
            raise EnvironmentError("Could not find a compatible terminal (e.g., gnome-terminal).")

    finally:
        if os.path.exists(COMMANDS_FILE_PATH):
            os.remove(COMMANDS_FILE_PATH)

def run_main_script():
    if not os.path.exists(MAIN_PY_PATH):
        raise FileNotFoundError(f"Main application file not found at {MAIN_PY_PATH}.")
    print(f"Attempting to start {MAIN_PY_PATH}...")
    subprocess.Popen(["python3", MAIN_PY_PATH])

# --- Hauptlogik ---

if __name__ == "__main__":
    try:
        online_hash = get_online_hash(SYS_TIWUT_URL)
        local_hash = get_local_hash(LOCAL_SYS_TIWUT)

        if local_hash is None or local_hash != online_hash:
            print("Update required. Starting process...")
            show_info_window("Downloading new files...", duration_ms=2000)
            download_file(SYS_TIWUT_URL, LOCAL_SYS_TIWUT)
            download_file(MAIN_PY_URL, MAIN_PY_PATH)
            make_executable(MAIN_PY_PATH)

            show_info_window("A new terminal will open for setup. Please enter your password there.", duration_ms=5000)
            execute_setup_commands_in_new_terminal()
            
            show_info_window("Update complete. Starting application...", duration_ms=2000)
            run_main_script()
        else:
            print("Application is up to date. Starting...")
            run_main_script()

    except Exception as e:
        error_message = f"An unexpected error occurred:\n{e}"
        print(error_message)
        show_info_window(error_message, duration_ms=15000)

    print("Launcher finished.")
    sys.exit()
