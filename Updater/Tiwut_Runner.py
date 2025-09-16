import subprocess
import os

# Definiert den Namen der auszuführenden Datei
executable_name = "Tiwut_Updater.exe"

# Holt den Pfad des Verzeichnisses, in dem das Skript ausgeführt wird
script_directory = os.path.dirname(os.path.abspath(__file__))

# Kombiniert den Verzeichnispfad und den Namen der ausführbaren Datei, um den vollständigen Pfad zu erhalten
executable_path = os.path.join(script_directory, executable_name)

print(f"Versuche, {executable_path} auszuführen...")

try:
    # Führt die externe .exe-Datei aus
    subprocess.run([executable_path], check=True)
    print(f"'{executable_name}' wurde erfolgreich gestartet.")
except FileNotFoundError:
    print(f"Fehler: '{executable_name}' wurde im selben Ordner nicht gefunden.")
except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")