#!/bin/bash

# Define variables for the paths to ensure the correct files are removed
APP_DIR="$HOME/.local/share/Tiwut/Tiwut-Launcher"
ICON_NAME="tiwut-launcher.png"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_FILE_DIR="$HOME/.local/share/applications"
DESKTOP_FILE_PATH="$DESKTOP_FILE_DIR/Tiwut-Launcher.desktop"
DESKTOP_SHORTCUT_PATH="$HOME/Desktop/Tiwut-Launcher.desktop"

echo "Starting the uninstallation of Tiwut-Launcher..."

# Remove the desktop shortcut
echo "Removing desktop shortcut..."
if [ -f "$DESKTOP_SHORTCUT_PATH" ]; then
    rm "$DESKTOP_SHORTCUT_PATH"
    echo "Desktop shortcut removed."
else
    echo "Desktop shortcut not found, skipping."
fi

# Remove the .desktop file from the applications directory
echo "Removing application menu entry..."
if [ -f "$DESKTOP_FILE_PATH" ]; then
    rm "$DESKTOP_FILE_PATH"
    echo "Application menu entry removed."
else
    echo "Application menu entry not found, skipping."
fi

# Remove the icon
echo "Removing application icon..."
if [ -f "$ICON_DIR/$ICON_NAME" ]; then
    rm "$ICON_DIR/$ICON_NAME"
    echo "Application icon removed."
else
    echo "Application icon not found, skipping."
fi

# Remove the application directory and its contents
echo "Removing application directory..."
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "Application directory removed."
else
    echo "Application directory not found, skipping."
fi

echo ""
echo "Uninstallation of Tiwut-Launcher is complete."
echo "You may need to log out and log back in for your application menu to refresh completely."