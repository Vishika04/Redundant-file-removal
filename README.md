<div align="center">
  <img src="assets/logo.png" alt="RedunClear Logo" width="600"/>
</div>

# 🗂 Redundant File Remover v3.0

> A fast, safe, professional desktop app to **find and remove duplicate files** — with a live Storage Tree View, SHA-256 content scanning, and always-safe Recycle Bin deletion.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python) ![PyQt6](https://img.shields.io/badge/UI-PyQt6-green) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/License-MIT-orange)

---

## ✨ Features

- ⚡ **Parallel SHA-256 scanning** — multi-threaded, blazing fast
- 🗂 **Storage Tree View** — visualise your folder structure as a collapsible tree with folder size rollups
- 🔒 **OS Safety Guards** — system/protected paths are automatically blocked from scanning and deletion
- ♻️ **Always uses Recycle Bin** — nothing is permanently deleted; restore anytime
- 🎨 **Modern dark UI** — GitHub-style dark theme with branch-line tree nodes
- 🖱️ **Right-click context menus** — open in Explorer, check/uncheck, delete individual files
- 🔍 **Multiple match modes** — Content Hash (SHA-256), File Name, or both

---

## 🚀 Installation (All Platforms)

### Prerequisites — Python 3.10 or newer

Check if you already have Python:
```bash
python --version
# or
python3 --version
```

If not installed, download from 👉 https://www.python.org/downloads/

> **Windows users:** During install, check ✅ **"Add Python to PATH"**

---

### Step 1 — Download the script

Save `redundant_file_remover.py` anywhere on your computer, e.g.:
- Windows: `C:\Users\YourName\Desktop\redundant_file_remover.py`
- macOS / Linux: `~/Desktop/redundant_file_remover.py`

---

### Step 2 — Install dependencies

Open a terminal (Command Prompt / PowerShell / Terminal) and run:

```bash
pip install PyQt6 send2trash
```

> If `pip` isn't found, try `pip3` instead.

---


### Step 3 — Run the app

```bash
python redundant_file_remover.py
```

> On macOS/Linux use `python3` if `python` points to Python 2.

---

## 🖥️ Install as a Proper Desktop App (Shortcut / Icon)

### 🪟 Windows — Create a Desktop Shortcut

1. Right-click your Desktop → **New → Shortcut**
2. In the location field, paste (adjust path as needed):
   ```
   pythonw "C:\Users\YourName\Desktop\redundant_file_remover.py"
   ```
   > Use `pythonw` (not `python`) to prevent a black terminal window from opening.
3. Click **Next**, name it `Redundant File Remover`, click **Finish**
4. Right-click the shortcut → **Properties → Change Icon** → browse for a custom icon if desired

**Or use the PowerShell one-liner** to create the shortcut automatically:
```powershell
$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$sc = $ws.CreateShortcut("$desktop\Redundant File Remover.lnk")
$sc.TargetPath = "pythonw"
$sc.Arguments = "`"$desktop\redundant_file_remover.py`""
$sc.WorkingDirectory = "$desktop"
$sc.Save()
```

---

### 🍎 macOS — Create an App Bundle with Automator

1. Open **Automator** (search in Spotlight)
2. Choose **New Document → Application**
3. Search for **"Run Shell Script"** and drag it to the workflow
4. Paste:
   ```bash
   python3 /Users/YourName/Desktop/redundant_file_remover.py
   ```
5. **File → Save** → name it `Redundant File Remover` → save to `/Applications`
6. Double-click the `.app` to launch — it will appear in your Dock!

---

### 🐧 Linux — Create a `.desktop` Launcher

1. Create the launcher file:
   ```bash
   nano ~/.local/share/applications/redundant-file-remover.desktop
   ```
2. Paste the following (adjust the path):
   ```ini
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=Redundant File Remover
   Comment=Find and remove duplicate files safely
   Exec=python3 /home/YourName/Desktop/redundant_file_remover.py
   Icon=utilities-file-archiver
   Terminal=false
   Categories=Utility;FileManager;
   ```
3. Save and make it executable:
   ```bash
   chmod +x ~/.local/share/applications/redundant-file-remover.desktop
   ```
4. It will now appear in your application menu!

---

## 📦 Bundle as a Standalone EXE (No Python Required)

Use **PyInstaller** to create a single `.exe` / binary that anyone can run — no Python needed.

### Install PyInstaller
```bash
pip install pyinstaller
```

### Build (Windows)
```bash
python -m PyInstaller --onefile --windowed --name "RedundantFileRemover" redundant_file_remover.py
```

### Build (macOS / Linux)
```bash
python3 -m PyInstaller --onefile --windowed --name "RedundantFileRemover" redundant_file_remover.py
```

The output will be in the `dist/` folder:
- **Windows:** `dist\RedundantFileRemover.exe` — share this with anyone!
- **macOS:** `dist/RedundantFileRemover` — or use `--windowed` for a `.app` bundle
- **Linux:** `dist/RedundantFileRemover` — single binary, no install needed

> **Tip:** Add `--icon=your_icon.ico` (Windows) or `--icon=your_icon.icns` (macOS) to set a custom icon.

---

## 🛡️ Safety Guarantees

| Protection | Details |
|---|---|
| **Recycle Bin only** | Files are never permanently deleted — always go to Trash/Recycle Bin |
| **System path guard** | `Windows`, `System32`, `Program Files`, `AppData`, `/usr`, `/etc` etc. are blocked |
| **Protected extensions** | `.exe`, `.dll`, `.sys`, `.bat`, `.ps1` and other OS files are flagged and deletion is disabled |
| **Confirmation dialog** | Every deletion requires an explicit Yes/No confirmation |
| **Protected items skipped** | Auto-select skips all protected files automatically |

---

## 📋 Usage Guide

1. **Click "Browse Folder"** in the sidebar to pick a directory
2. **Configure filters** — match mode, min size, extensions
3. **Click "Start Scan"** — duplicates appear as grouped tree nodes
4. **Check files** to mark for deletion (or use "Select Dupes" to auto-check)
5. **Click "Move to Recycle Bin"** — files are safely removed and recoverable
6. **Switch to Storage Tree View tab** → click "Load Tree" to explore your folder visually

---

## 🔧 Requirements

| Package | Version | Purpose |
|---|---|---|
| `PyQt6` | ≥ 6.4 | GUI framework |
| `send2trash` | ≥ 1.8 | Safe Recycle Bin deletion |

All other imports (`os`, `hashlib`, `pathlib`, etc.) are Python standard library — no extra install needed.

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*A5A9
