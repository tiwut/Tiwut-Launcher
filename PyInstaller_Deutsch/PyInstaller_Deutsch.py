import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

def browse_file(entry):
    """Öffnet einen Dialog zur Auswahl einer Datei und füllt das Eingabefeld."""
    filename = filedialog.askopenfilename(
        filetypes=[("Python Files", "*.py")]
    )
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)

def browse_icon(entry):
    """Öffnet einen Dialog zur Auswahl einer Icon-Datei und füllt das Eingabefeld."""
    filename = filedialog.askopenfilename(
        filetypes=[("Icon Files", "*.ico")]
    )
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)

def run_pyinstaller():
    """Baut den PyInstaller-Befehl zusammen und führt ihn aus."""
    script_path = entry_script.get()
    icon_path = entry_icon.get()
    onefile = onefile_var.get()
    noconsole = noconsole_var.get()

    if not script_path:
        messagebox.showerror("Fehler", "Bitte wählen Sie eine Python-Datei aus.")
        return

    command = ["python", "-m", "PyInstaller"]

    if onefile:
        command.append("--onefile")
    
    if noconsole:
        command.append("--noconsole")
    
    if icon_path:
        command.extend(["--icon", icon_path])

    command.append(script_path)
    
    try:
        messagebox.showinfo("PyInstaller", "Vorgang gestartet. Überprüfen Sie das Terminal für den Fortschritt.")
        
        # Führt den Befehl aus und leitet die Ausgabe um
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            messagebox.showinfo("Erfolg", "EXE-Datei erfolgreich erstellt!")
            print("--- PyInstaller Ausgabe ---")
            print(stdout)
        else:
            messagebox.showerror("Fehler", f"Fehler bei der Erstellung der EXE.\n\nDetails:\n{stderr}")
    except FileNotFoundError:
        messagebox.showerror("Fehler", "PyInstaller oder Python wurde nicht gefunden. Stellen Sie sicher, dass sie im PATH sind oder verwenden Sie 'python -m PyInstaller'.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Ein unbekannter Fehler ist aufgetreten: {e}")

# --- GUI-Fenster erstellen ---
root = tk.Tk()
root.title("PyInstaller GUI")
root.geometry("500x400")
root.resizable(False, False)

# --- Widgets ---
frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True, fill="both")

# Python-Skript
label_script = tk.Label(frame, text="Python-Skript (*.py):", anchor="w")
label_script.pack(fill="x", pady=(0, 5))
entry_script = tk.Entry(frame, width=50)
entry_script.pack(fill="x")
btn_browse_script = tk.Button(frame, text="Durchsuchen", command=lambda: browse_file(entry_script))
btn_browse_script.pack(pady=(5, 10))

# Icon-Datei
label_icon = tk.Label(frame, text="Icon-Datei (*.ico):", anchor="w")
label_icon.pack(fill="x", pady=(10, 5))
entry_icon = tk.Entry(frame, width=50)
entry_icon.pack(fill="x")
btn_browse_icon = tk.Button(frame, text="Durchsuchen", command=lambda: browse_icon(entry_icon))
btn_browse_icon.pack(pady=(5, 10))

# Optionen
onefile_var = tk.BooleanVar(value=True)
check_onefile = tk.Checkbutton(frame, text="Einzelne EXE-Datei (--onefile)", variable=onefile_var)
check_onefile.pack(anchor="w", pady=(10, 5))

noconsole_var = tk.BooleanVar(value=False)
check_noconsole = tk.Checkbutton(frame, text="Kein Terminal/Konsole (--noconsole)", variable=noconsole_var)
check_noconsole.pack(anchor="w")

# Button zum Erstellen
btn_run = tk.Button(root, text="EXE erstellen", command=run_pyinstaller, font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white")
btn_run.pack(pady=20)

root.mainloop()