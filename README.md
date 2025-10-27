# 🚀 Tiwut-Launcher

The **Tiwut-Launcher** is the official desktop client designed to provide easy access to all applications developed as part of the **Tiwut** hobby project. It functions as an application store and launcher, allowing users to discover, install, and manage Tiwut's desktop applications.

The Tiwut project's full collection of repositories can be found on GitHub: [https://github.com/tiwut?tab=repositories](https://github.com/tiwut?tab=repositories)

## ✨ Features

* **Application Hub:** Centralized access to all desktop applications from the Tiwut hobby project.
* **Cross-Platform Support:** Dedicated versions for both Windows and Linux, built from separate source files (`v2.5stable.py` for Windows and `main.py` for Linux).
* **Intuitive UI:** Built using `tkinter` and `ttk` to provide a clean application store experience.
* **Linux Edition Adapations (in `main.py`):**
    * Uses Linux-standard directories (`~/.config`, `~/.local/share`) for application data.
    * Creates `.desktop` files for application shortcuts.
    * Uses Linux-standard executable names ("main" instead of "main.exe").
* **Installation/Uninstallation:** Manage your installed Tiwut applications directly through the launcher.

## 💻 Installation

The Tiwut-Launcher is provided with platform-specific installers in the GitHub Releases section.

**Latest Releases:** [https://github.com/tiwut/Tiwut-Launcher/releases](https://github.com/tiwut/Tiwut-Launcher/releases)

### Windows

Download and run the installer (`.exe` installer) from the official GitHub releases page.

### Linux (Debian/Ubuntu-based systems)

A shell script installer is provided for convenience.

1.  Download the `install-tiwut-launcher.sh` script from the latest [GitHub Releases](https://github.com/tiwut/Tiwut-Launcher/releases).
2.  Open a terminal, navigate to the download directory, and execute the script:

    ```bash
    chmod +x install-tiwut-launcher.sh
    ./install-tiwut-launcher.sh
    ```

    The script downloads the main Python application file (`main.py`), makes it executable, and creates standard application and desktop shortcuts.

## 🛠️ Source Code

The project is written in Python with a graphical interface powered by `tkinter`.

| Platform | Source File | Description |
| :--- | :--- | :--- |
| **Linux Edition** | `main.py` | Source code specifically adapted for Linux systems (using Linux directories and standards). |
| **Windows Edition** | `v2.5stable.py` | Source code for the Windows version (uses Windows-specific directories and naming conventions). |

## 🔗 Project Links

* **Tiwut Project Repositories:** [https://github.com/tiwut?tab=repositories](https://github.com/tiwut?tab=repositories)
