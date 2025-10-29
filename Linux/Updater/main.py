import os
import urllib.request
import hashlib
import tkinter as tk
from tkinter import ttk
import sys
import subprocess

# --- Konfiguration ---
SYS_TIWUT_URL = "https://launcher.tiwut.de/Linux/sys.tiwut"
MAIN_PY_URL = "https://launcher.tiwut.de/Linux/Launcher/main.py"
SYS_MODUL_URL = "https://launcher.tiwut.de/Linux/Updater/sys_modul.tiwut"
LOCAL_SYS_TIWUT = "sys.tiwut"
LAUNCHER_DIR = "Launcher"
MAIN_PY_PATH = os.path.join(LAUNCHER_DIR, "main.py")

# --- Funktionen ---

def show_info_window(message):
    """Zeigt ein einfaches Informationsfenster an."""
    root = tk.Tk()
    root.title("Process Info")
    root.geometry("300x100")
    label = ttk.Label(root, text=message)
    label.pack(pady=20, padx=20)
    root.after(3000, root.destroy)  # Schließt das Fenster nach 3 Sekunden
    root.mainloop()

def get_online_hash(url):
    """Ruft den SHA-256-Hash des Inhalts von einer URL ab."""
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = response.read()
                return hashlib.sha256(data).hexdigest()
    except Exception as e:
        print(f"Error fetching online hash: {e}")
        return None

def get_local_hash(filepath):
    """Berechnet den SHA-256-Hash einer lokalen Datei."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        data = f.read()
        return hashlib.sha256(data).hexdigest()

def download_file(url, local_path):
    """Lädt eine Datei von einer URL an einen lokalen Speicherort herunter."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        urllib.request.urlretrieve(url, local_path)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def make_executable(filepath):
    """Macht eine Datei unter Linux ausführbar."""
    try:
        os.chmod(filepath, 0o755)
        return True
    except Exception as e:
        print(f"Error making {filepath} executable: {e}")
        return False

def install_modules():
    """Installiert Python-Module, die in sys_modul.tiwut aufgeführt sind."""
    if download_file(SYS_MODUL_URL, "sys_modul.tiwut"):
        try:
            with open("sys_modul.tiwut", "r") as f:
                modules = f.read().splitlines()
            for module in modules:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            os.remove("sys_modul.tiwut") # Bereinigen
        except Exception as e:
            print(f"Error installing modules: {e}")

def run_main_script():
    """Führt das Haupt-Python-Skript aus."""
    if os.path.exists(MAIN_PY_PATH):
        try:
            subprocess.run(["python3", MAIN_PY_PATH])
        except Exception as e:
            print(f"Error running {MAIN_PY_PATH}: {e}")
    else:
        print(f"Error: {MAIN_PY_PATH} not found.")

# --- Hauptlogik ---

if __name__ == "__main__":
    local_hash = get_local_hash(LOCAL_SYS_TIWUT)
    online_hash = get_online_hash(SYS_TIWUT_URL)

    update_needed = False
    if local_hash is None:
        update_needed = True
        show_info_window("sys.tiwut not found. Updating...")
    elif local_hash != online_hash:
        update_needed = True
        show_info_window("sys.tiwut is outdated. Updating...")

    if update_needed:
        # Update-Prozess
        print("Starting update...")
        if download_file(SYS_TIWUT_URL, LOCAL_SYS_TIWUT) and \
           download_file(MAIN_PY_URL, MAIN_PY_PATH) and \
           make_executable(MAIN_PY_PATH):
            print("Update successful.")
            install_modules()
            run_main_script()
        else:
            print("Update failed.")
    else:
        # Direktes Starten
        print("sys.tiwut is up to date. Starting application...")
        run_main_script()

    sys.exit()