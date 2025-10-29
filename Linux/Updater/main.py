import os
import urllib.request
import hashlib
import tkinter as tk
from tkinter import ttk
import sys
import subprocess

# --- Configuration ---
SYS_TIWUT_URL = "https://launcher.tiwut.de/Linux/sys.tiwut"
MAIN_PY_URL = "https://launcher.tiwut.de/Linux/Launcher/main.py"
COMMANDS_URL = "https://launcher.tiwut.de/Linux/Updater/sys_modul.tiwut"
LOCAL_SYS_TIWUT = "sys.tiwut"
LAUNCHER_DIR = "Launcher"
MAIN_PY_PATH = os.path.join(LAUNCHER_DIR, "main.py")



def show_info_window(message):
    """Displays a simple information window."""
    root = tk.Tk()
    root.title("Process Info")
    root.geometry("350x100")
    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    label = ttk.Label(root, text=message, wraplength=330)
    label.pack(pady=20, padx=20)
    root.after(3500, root.destroy)  # Close the window after 3.5 seconds
    root.mainloop()

def get_online_hash(url):
    """Gets the SHA-256 hash of content from a URL."""
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = response.read()
                return hashlib.sha256(data).hexdigest()
    except Exception as e:
        print(f"Error fetching online hash from {url}: {e}")
        return None

def get_local_hash(filepath):
    """Calculates the SHA-256 hash of a local file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        data = f.read()
        return hashlib.sha256(data).hexdigest()

def download_file(url, local_path):
    """Downloads a file from a URL to a local path."""
    try:
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        urllib.request.urlretrieve(url, local_path)
        print(f"Successfully downloaded {local_path} from {url}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def make_executable(filepath):
    """Makes a file executable on Linux."""
    try:
        # Corresponds to chmod 755
        os.chmod(filepath, 0o755)
        print(f"Made {filepath} executable.")
        return True
    except Exception as e:
        print(f"Error making {filepath} executable: {e}")
        return False

def execute_setup_commands():
    """Downloads and executes commands from the commands file."""
    commands_file = "sys_modul.tiwut"
    print("Downloading setup commands file...")
    if download_file(COMMANDS_URL, commands_file):
        try:
            print("--- Executing Setup Commands ---")
            with open(commands_file, "r") as f:
                commands = f.read().splitlines()
            for command in commands:
                command = command.strip()
                if command and not command.startswith('#'): # Ignore empty lines and comments
                    print(f"Executing command: '{command}'")
                    # Using shell=True to interpret the command as a string
                    # check=True will raise an error if the command fails
                    subprocess.run(command, shell=True, check=True)
            print("--- Finished Executing Commands ---")
        except FileNotFoundError:
            print(f"Error: Could not find the commands file '{commands_file}'.")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: '{e.cmd}'. It returned a non-zero exit code: {e.returncode}")
            print("Please check the command and your permissions (try running with sudo).")
        except Exception as e:
            print(f"An unexpected error occurred while executing commands: {e}")
        finally:
            # Clean up the downloaded commands file
            os.remove(commands_file)

def run_main_script():
    """Runs the main python script."""
    if os.path.exists(MAIN_PY_PATH):
        print(f"Attempting to start {MAIN_PY_PATH}...")
        try:
            # Run the script and exit this launcher
            subprocess.run(["python3", MAIN_PY_PATH], check=True)
        except FileNotFoundError:
             print(f"Error: 'python3' command not found. Please ensure Python 3 is installed and in your PATH.")
        except Exception as e:
            print(f"Error running {MAIN_PY_PATH}: {e}")
    else:
        print(f"Error: Main application file not found at {MAIN_PY_PATH}.")

# --- Main Logic ---

if __name__ == "__main__":
    online_hash = get_online_hash(SYS_TIWUT_URL)
    local_hash = get_local_hash(LOCAL_SYS_TIWUT)


    update_needed = False
    if online_hash is None:
        print("Warning: Could not connect to update server. Will try to run the local version if available.")
    elif local_hash is None:
        update_needed = True
        show_info_window("Application not found. Starting download...")
    elif local_hash != online_hash:
        update_needed = True
        show_info_window("A new version is available. Updating...")

    if update_needed:
        # --- Update Process ---
        print("Starting update process...")
        show_info_window("Updating... Please wait.")
        
        # Download core files
        download_success = download_file(SYS_TIWUT_URL, LOCAL_SYS_TIWUT) and \
                           download_file(MAIN_PY_URL, MAIN_PY_PATH)

        if download_success:
            make_executable(MAIN_PY_PATH)
            
            execute_setup_commands()
            # Finally, run the main script
            run_main_script()
        else:
            print("Update failed. Could not download necessary files.")
            show_info_window("Update failed. Please check your internet connection.")
    else:
        # --- Start Directly ---
        print("Application is up to date. Starting...")
        run_main_script()

    print("Launcher finished.")
    sys.exit()
