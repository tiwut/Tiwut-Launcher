# PyToExePro
PyToExePro


### **Py-to-EXE-Pro – User Manual**

**Version 1.1**

Welcome to Py-to-EXE-Pro! This manual guides you through all the application's features so you can effortlessly convert your Python scripts into standalone Windows programs (.exe).

#### **1. Introduction: What is Py-to-EXE-Pro?**

Py-to-EXE-Pro is a graphical user interface (GUI) for the powerful command-line tool **PyInstaller**. It was designed to make the EXE creation process as simple and transparent as possible, especially for developers who don't want to deal with the command line.

With just a few clicks, you can:
* Select your Python script.
* Specify important options such as the output format and a custom icon.
* Watch the creation process live.
* Receive a finished .exe file at the end that you can share with others.

#### **2. System Requirements**

For Py-to-EXE-Pro to function properly, your system must have the following:

* **Windows operating system** (7, 8, 10, 11)
* **Python** must be installed and added to the system PATH. (This is a default option during Python installation).
* **pip**, the Python package manager, must be functional.

#### **3. Step-by-Step Instructions**

The application interface is divided into logical steps.

##### **Step 1: System Check and Dependencies**

Before you can begin, the PyInstaller tool must be installed on your system.

1. **Status Indicator:** Immediately after launch, the application checks whether PyInstaller is available.
* <span style="color:green;">**Green (Ready to build!):**</span> Everything is ready. PyInstaller was found.
* <span style="color:red;">**Red (PyInstaller not found!):**</span> PyInstaller is missing. You cannot continue until it is installed.

2. **Button "Show Install Instructions":** If the status is red, click this button. A window will open with simple instructions:
* Open a command prompt (CMD) or PowerShell.
* Run the command `pip install pyinstaller`.
* Restart Py-to-EXE-Pro after installation.

##### **Step 2: Select Your Script**

1. **Python Script (.py):** This is the core of your application.
2. **Browse...:** Click this button to open the file explorer and select your main Python script (e.g., `main.py` or `app.py`). The path will be automatically entered into the text field.

##### **Step 3: Configure Build Options**

Here you specify *how* your .exe file should be created.

* **Output Type:**
* **One-File (.exe):** Creates a single, standalone .exe file. This is ideal for easy sharing. The first launch may take a little longer as the files need to be temporarily unpacked.
* **One-Directory (Folder):** Creates a folder containing the .exe file along with all dependencies (DLLs, etc.). This method often has a faster startup time.

* **Console:**
* **Windowless (for GUI):** Choose this for graphical applications (e.g., with Tkinter, PyQt, CustomTkinter). No black console window will be displayed in the background.
* **Show Console Window:** **Select this for scripts that produce text output** or don't have their own graphical interface. If you select this option for a GUI program, a console window will appear in the background, which can be useful for debugging.

* **Icon File (.ico):**
* **Browse...:** Select an icon file in the .ico format to give your application a professional look.
* **Clear:** Removes the icon from the list.

##### **Step 4: Create the Executable**

1. **BUILD .EXE:** Once all settings have been made, click this button to start the process. The button will be disabled during the process.

2. **Progress & Log:**
* **Progress Bar:** Shows you roughly what stage the build process is currently at.


* **Log Window:** Here you can see the **live output** from PyInstaller. This is extremely useful for tracking progress in detail and for viewing error messages in case something goes wrong.

3. **Open Output Folder:** Once the process has completed successfully, this button becomes active. Clicking it opens the `dist` folder containing your finished `.exe` file. This folder will be created in the same directory as your original Python script.

#### **4. Troubleshooting**

Sometimes things don't go as planned. Here are solutions to common problems:

* **Problem:** My created .exe file is flagged as a virus by my antivirus program.
* **Solution:** This is a common "false positive" error. PyInstaller bundles a script with an interpreter, which makes some antivirus programs suspicious. If you trust the code, create an exception in your antivirus program. For a second opinion, you can upload your .exe file to VirusTotal.com (https://www.virustotal.com/).

* **Problem:** The .exe file starts and closes immediately.
* **Solution:** This almost always means your script encountered an error. Recreate the .exe file, but this time select the "Show Console Window" option. When you now run the .exe file, the console window remains open long enough to read the error message.

* **Problem:** The .exe reports a ModuleNotFoundError, even though the module is installed on my PC.
* **Solution:** PyInstaller sometimes doesn't recognize "hidden" imports. You have to manually tell PyInstaller to include this module. Unfortunately, this isn't possible via the GUI. You would have to run PyInstaller from the command line with the --hidden-import MODULENAME option.

* **Problem:** My .exe can't find its associated files (images, configuration files).
* **Solution:** When an .exe file is run, its "working directory" is not necessarily the same as that of your script. Relative paths like img/logo.png no longer work. You must use absolute paths. A tried-and-tested code snippet for finding the path to the .exe is:
python
import sys
import os

if getattr(sys, 'frozen', False):
# When running as .exe
application_path = os.path.dirname(sys.executable)
else:
# When running as .py script
application_path = os.path.dirname(__file__)

# Example of accessing a file
path_to_logo = os.path.join(application_path, 'data', 'logo.png')


You must manually copy the additional files (data folder) into the dist folder next to your .exe.
