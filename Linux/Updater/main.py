import os
import urllib.request
import hashlib
import tkinter as tk
from tkinter import ttk
import sys
import subprocess
import ssl
import shutil

# --- Configuration ---
# All URLs now use http as requested to avoid potential redirect/SSL issues.
SYS_TIWUT_URL = "http://launcher.tiwut.de/Linux/sys.tiwut"
MAIN_PY_URL = "http://launcher.tiwut.de/Linux/Launcher/main.py"
COMMANDS_URL = "http://launcher.tiwut.de/Linux/Updater/sys_modul.tiwut"
LOCAL_SYS_TIWUT = "sys.tiwut"
LAUNCHER_DIR = "Launcher"
MAIN_PY_PATH = os.path.join(LAUNCHER_DIR, "main.py")

# --- SSL Context (still good practice in case a URL is changed back to https) ---
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    pass

# --- Functions ---

def show_info_window(message, duration_ms=4000):
    """Displays a simple information window."""
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
    """Gets the SHA-256 hash of content from a URL."""
    try:
        with urllib.request.urlopen(url, context=ssl_context) as response:
            if response.status == 200:
                return hashlib.sha256(response.read()).hexdigest()
    except Exception as e:
        raise ConnectionError(f"Could not fetch hash from {url}: {e}")

def get_local_hash(filepath):
    """Calculates the SHA-256 hash of a local file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def download_file(url, local_path):
    """
    Downloads a file with improved error handling to distinguish between
    network and filesystem errors.
    """
    # Step 1: Download data into memory
    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, context=ssl_context) as response:
            if response.status != 200:
                raise ConnectionError(f"Server returned status {response.status}")
            data = response.read()
    except Exception as e:
        # If this part fails, it's a network-related problem.
        raise ConnectionError(f"Network error while downloading {url}: {e}")

    # Step 2: Write the downloaded data to a local file
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as out_file:
            out_file.write(data)
    except Exception as e:
        # If this part fails, it's a filesystem (permissions, invalid path) problem.
        raise IOError(f"Filesystem error while saving to {local_path}: {e}")

    print(f"Successfully downloaded {local_path} from {url}")

def make_executable(filepath):
    """Makes a file executable on Linux."""
    try:
        os.chmod(filepath, 0o755)
        print(f"Made {filepath} executable.")
    except Exception as e:
        raise OSError(f"Could not make {filepath} executable: {e}")

def execute_setup_commands_in_new_terminal():
    """
    Downloads a command file and executes it in a new terminal window,
    allowing interactive password entry.
    """
    commands_file = "sys_modul.tiwut"
    print("Downloading setup commands file...")
    download_file(COMMANDS_URL, commands_file)

    try:
        with open(commands_file, "r") as f:
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
            raise EnvironmentError("Could not find a compatible terminal (e.g., gnome-terminal). Please run setup commands manually.")

    finally:
        if os.path.exists(commands_file):
            os.remove(commands_file)

def run_main_script():
    """Runs the main python script."""
    if not os.path.exists(MAIN_PY_PATH):
        raise FileNotFoundError(f"Main application file not found at {MAIN_PY_PATH}.")
    print(f"Attempting to start {MAIN_PY_PATH}...")
    subprocess.Popen(["python3", MAIN_PY_PATH])

# --- Main Logic ---

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
        # The new, more specific error messages will be displayed here.
        error_message = f"An unexpected error occurred:\n{e}"
        print(error_message)
        show_info_window(error_message, duration_ms=15000)

    print("Launcher finished.")
    sys.exit()
