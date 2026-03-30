#!/usr/bin/env bash
# =====================================================
#  Redundant File Remover v3.0 — macOS / Linux Installer
# =====================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ============================================"
echo "   REDUNDANT FILE REMOVER  v3.0  Installer"
echo "  ============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] python3 not found."
    echo "  Install it from https://www.python.org/downloads/"
    exit 1
fi
echo "  [OK] $(python3 --version) found."

# Install dependencies
echo ""
echo "  Installing Python dependencies..."
python3 -m pip install --upgrade pip -q
python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
echo "  [OK] Dependencies installed."

# Make run.sh executable
chmod +x "$SCRIPT_DIR/run.sh"

# Linux: create .desktop launcher
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DESKTOP_FILE="$HOME/.local/share/applications/redundant-file-remover.desktop"
    mkdir -p "$HOME/.local/share/applications"
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Redundant File Remover
GenericName=Duplicate File Cleaner
Comment=Find and remove duplicate files safely
Exec=python3 $SCRIPT_DIR/redundant_file_remover.py
Icon=utilities-file-archiver
Terminal=false
StartupNotify=true
Categories=Utility;FileManager;System;
EOF
    chmod +x "$DESKTOP_FILE"
    echo "  [OK] App launcher added to your applications menu."
fi

# macOS: create Automator app
if [[ "$OSTYPE" == "darwin"* ]]; then
    APP_DIR="/Applications/Redundant File Remover.app"
    MACOS_DIR="$APP_DIR/Contents/MacOS"
    mkdir -p "$MACOS_DIR"
    cat > "$MACOS_DIR/launch" <<EOF
#!/bin/bash
python3 "$SCRIPT_DIR/redundant_file_remover.py"
EOF
    chmod +x "$MACOS_DIR/launch"
    cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Redundant File Remover</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.redundantfileremover</string>
    <key>CFBundleVersion</key>
    <string>3.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
    echo "  [OK] App bundle created at /Applications/Redundant File Remover.app"
fi

echo ""
echo "  ============================================"
echo "   Installation complete!"
echo "   Run with:  bash $SCRIPT_DIR/run.sh"
echo "  ============================================"
echo ""
