#!/bin/bash

APP_DIR="$HOME/.local/share/Tiwut/Tiwut-Launcher"
APP_URL="https://launcher.tiwut.de/Linux/Updater/main.py"
ICON_URL="https://launcher.tiwut.de/Linux/icon.png"
ICON_NAME="tiwut-launcher.png"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_FILE_DIR="$HOME/.local/share/applications"
DESKTOP_FILE_PATH="$DESKTOP_FILE_DIR/Tiwut-Launcher.desktop"
DESKTOP_SHORTCUT_PATH="$HOME/Desktop/Tiwut-Launcher.desktop"

echo "Erstelle Anwendungsverzeichnisse..."
mkdir -p "$APP_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$DESKTOP_FILE_DIR"


echo "Download the application..."
if ! wget -O "$APP_DIR/main.py" "$APP_URL"; then
    echo "Error downloading the application. Please check the URL and your internet connection."
    exit 1
fi

echo "Make the application executable..."
chmod +x "$APP_DIR/main.py"

if ! sed -i '1i#!/usr/bin/env python3' "$APP_DIR/main.py"; then
    echo "Error adding shebang line to Python file."
    exit 1
fi


echo "Download the application icon (.png)..."
if ! wget -O "$ICON_DIR/$ICON_NAME" "$ICON_URL"; then
    echo "Error downloading icon. Please check the URL and your internet connection."
    exit 1
fi


echo "Create application launchers..."
cat > "$DESKTOP_FILE_PATH" << EOL
[Desktop Entry]
Version=1.0
Name=Tiwut-Launcher
Comment=Startet den Tiwut-Launcher
Exec=python3 "$APP_DIR/main.py"
Icon=$ICON_DIR/$ICON_NAME
Terminal=false
Type=Application
Categories=Utility;Application;
EOL


chmod +x "$DESKTOP_FILE_PATH"


echo "Create desktop shortcut..."

if [ -d "$HOME/Desktop" ]; then
    ln -s "$DESKTOP_FILE_PATH" "$DESKTOP_SHORTCUT_PATH"
else
    echo "Desktop directory not found. You can launch the application from the Applications menu."
fi

echo "The installation of the Tiwut launcher is complete!"
echo "You may need to log out and log back in for the icon to display correctly."
