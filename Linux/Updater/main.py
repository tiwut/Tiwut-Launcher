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
SYS_TIWUT_URL = "https://launcher.tiwut.de/Linux/sys.tiwut"
MAIN_PY_URL = "https://launcher.tiwut.de/Linux/Launcher/main.py"
COMMANDS_URL = "https://launcher.tiwut.de/Linux/Updater/sys_modul.tiwut"
LOCAL_SYS_TIWUT = "sys.tiwut"
LAUNCHER_DIR = "Launcher"
MAIN_PY_PATH = os.path.join(LAUNCHER_DIR, "main.py")

# --- SSL CERTIFICATE BYPASS ---
# Creates a context that does not verify SSL certificates to avoid
# "CERTIFICATE_VERIFY_FAILED" errors.
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    pass

# --- Functions ---

def show_info_window(message, duration_ms=4000):
    """Displays a simple information window."""
    root = tk.Tk()
    root.title("Process Info")
    root.geometry("500x150")
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f'+{x}+{y}')
    label = ttk.Label(root, text=message, wraplength=480, justify='center')
    label.pack(pady=20, padx=20, expand=True)
    root.after(duration_ms, root.destroy)
    root.mainloop()

def get_online_hash(url):
    """Gets the SHA-256 hash of content from a URL, bypassing SSL verification."""
    try:
        with urllib.request.urlopen(url, context=ssl_context) as response:
            if response.status == 200:
                return hashlib.sha256(response.read()).hexdigest()
    except Exception as e:
        raise ConnectionError(f"Could not fetch online hash from {url}: {e}")

def get_local_hash(filepath):
    """Calculates the SHA-256 hash of a local file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def download_file(url, local_path):
    """Downloads a file robustly, bypassing SSL verification."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, context=ssl_context) as response:
            if response.status != 200:
                raise ConnectionError(f"Server returned status {response.status}")
            with open(local_path, 'wb') as out_file:
                out_file.write(response.read())
        print(f"Successfully downloaded {local_path} from {url}")
        return True
    except Exception as e:
        raise IOError(f"Failed to download {url}: {e}")

def make_executable(filepath):
    """Makes a file executable on Linux."""
    try:
        os.chmod(filepath, 0o755)
        print(f"Made {filepath} executable.")
    except Exception as e:
        raise OSError(f"Could not make {filepath} executable: {e}")

def execute_setup_commands_in_new_terminal():
    """
    Downloads a command file and executes its contents in a new terminal window.
    This allows the user to enter their sudo password interactively.
    """
    commands_file = "sys_modul.tiwut"
    print("Downloading setup commands file...")
    download_file(COMMANDS_URL, commands_file)

    try:
        with open(commands_file, "r") as f:
            # Read commands, filter out empty lines/comments
            commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        if not commands:
            print("No setup commands to execute.")
            return

        # Add a command to update package lists as a good practice
        full_command_string = "sudo apt-get update && " + " && ".join(commands)

        # Add messages for the user and a pause to keep the terminal open
        # The 'read' command waits for the user to press Enter.
        shell_script = (
            f'echo "--- Automated Setup ---";'
            f'echo "The application needs to install system packages.";'
            f'echo "Please enter your password when prompted.";'
            f'echo "Executing: {full_command_string}";'
            f'{full_command_string};'
            f'echo "";'
            f'echo "--- Setup Finished ---";'
            f'read -p "You can now close this terminal. Press ENTER to continue...";'
        )

        # List of common terminal emulators and their command execution flags
        terminals = [
            ('gnome-terminal', '--', '/bin/bash', '-c', shell_script),
            ('konsole', '-e', '/bin/bash', '-c', shell_script),
            ('xfce4-terminal', '-e', shell_script),
            ('xterm', '-e', shell_script)
        ]

        terminal_found = False
        for term_cmd in terminals:
            # shutil.which checks if a program exists in the system's PATH
            if shutil.which(term_cmd[0]):
                print(f"Found '{term_cmd[0]}'. Opening new terminal for setup...")
                # Start the terminal process and let it run independently
                subprocess.Popen(term_cmd)
                terminal_found = True
                break
        
        if not terminal_found:
            raise EnvironmentError("Could not find a compatible terminal (gnome-terminal, konsole, etc.). Please run setup commands manually.")

    finally:
        if os.path.exists(commands_file):
            os.remove(commands_file)

def run_main_script():
    """Runs the main python script."""
    if not os.path.exists(MAIN_PY_PATH):
        raise FileNotFoundError(f"Main application file not found at {MAIN_PY_PATH}.")
    print(f"Attempting to start {MAIN_PY_PATH}...")
    # We use Popen so the launcher can exit while the main app runs
    subprocess.Popen(["python3", MAIN_PY_PATH])

# --- Main Logic ---

if __name__ == "__main__":
    try:
        online_hash = get_online_hash(SYS_TIWUT_URL)
        local_hash = get_local_hash(LOCAL_SYS_TIWUT)

        update_needed = False
        if local_hash is None or local_hash != online_hash:
            update_needed = True

        if update_needed:
            print("Update required. Starting process...")
            show_info_window("Downloading new files...", duration_ms=2000)
            download_file(SYS_TIWUT_URL, LOCAL_SYS_TIWUT)
            download_file(MAIN_PY_URL, MAIN_PY_PATH)
            make_executable(MAIN_PY_PATH)

            show_info_window("A new terminal will open for setup. Please enter your password there.", duration_ms=5000)
            execute_setup_commands_in_new_terminal()
            
            # The script will wait here while the user handles the terminal window.
            # However, since the terminal is opened with Popen, our script *could* continue.
            # For a better user experience, we assume the user finishes before starting the main app.
            show_info_window("Update complete. Starting application...", duration_ms=2000)
            run_main_script()
        else:
            print("Application is up to date. Starting...")
            run_main_script()

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        show_info_window(error_message, duration_ms=10000)

    print("Launcher finished.")
    sys.exit()
