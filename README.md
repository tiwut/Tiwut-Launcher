# Tiwut Launcher
**Version 4**
The **Tiwut Launcher** is the official desktop client designed to provide easy access to all applications developed as part of the Tiwut hobby project. It functions as an application store and launcher, allowing users to discover, install, and manage Tiwut's desktop applications seamlessly.

Powered by the **Nexus** interpreter.

## Features

- **App Library:** Browse, discover, and install applications developed by the Tiwut Project directly from the cloud.
- **App Management:** One-click installation, launching, and uninstallation of your favorite applications.
- **Nexus Interpreter Integration:** Automatically handles application execution using the custom Nexus script interpreter.
- **Modern UI:** A clean, glassmorphism-inspired dark theme designed for a modern desktop experience.
- **In-App Updates:** Keep your Nexus interpreter up-to-date directly from the Launcher's settings menu.
- **Quick Search:** Find apps instantly using the built-in search bar.

## Getting Started

### Prerequisites

- C++17 compatible compiler
- Qt 6 (Core, Gui, Widgets, Network modules)
- CMake 3.16 or higher

### Build Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/tiwut/Tiwut-Launcher.git
   cd Tiwut-Launcher
   ```

2. Create a build directory and configure the project:
   ```bash
   mkdir build && cd build
   cmake ..
   ```

3. Compile the project:
   ```bash
   make
   ```

4. Run the Launcher:
   ```bash
   ./NexusLauncher
   ```
   *(Note: Ensure that the `nexus` executable is located in the same directory as the launcher, or update it directly via the in-app settings menu).*

## Project Details

- **Version:** v4.1.2
- **Developer:** Tiwut
- **Website:** [tiwut.org](https://tiwut.org)

## License

This project is licensed under the MIT License. 

Copyright (c) 2026 Tiwut

---

*Developed with ❤️ by the Tiwut Project.*
