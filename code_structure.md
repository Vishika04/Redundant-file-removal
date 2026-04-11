# Code Structure & Architecture
**Redundant File Remover v3.1**

This document explains the internal architecture of the project. The codebase recently transitioned from a single monolithic file (`redundant_file_remover.py`) into a highly modular, decoupled architecture organized by functional features.

---

## Architecture Basics

The app strictly follows the **Controller + Feature Modules** pattern:
1. **Views (UI)** never contain business logic and never make decisions. They only present data and emit signals.
2. **Workers** never touch UI widgets. They run on background threads and emit purely data-driven signals.
3. **Orchestrator (`MainWindow`)** sits in the middle. It instantiates the UI, spawns the workers, catches the button clicks, asks the core logic what to do, and instructs the UI what to display.

---

## Directory Layout

### 1. Root Files
- **`main.py`**
  The actual application entry point. Sets up the Qt Application, loads the dark theme palette globally, and instantiates the `MainWindow`.
- **`main_window.py`**
  The central nervous system. It creates instances of the header, sidebar, and tabs. It binds button clicks (like "Start Scan") to functions, initiates threading via `ScanWorker` and `StorageWorker`, and executes the system-sensitive deletion logic blocks.
- **`redundant_file_remover.py`**
  *(Deprecated)*. The original 1,000+ line monolith. Kept purely for historical reference and contains a prominent warning header.

### 2. `features/core/` (Foundational Logic)
No file in this folder is allowed to import a Qt GUI widget.
- **`constants.py`**
  Holds hardcoded settings like `GROUP_COLORS` (UI hex codes), `PROTECTED_ROOTS` (Windows system paths), and `PROTECTED_EXTS` (executables like `.exe`, `.bat`).
- **`models.py`**
  Contains lightweight `dataclass` definitions: `FileEntry` (representing a single file on disk) and `DuplicateGroup` (a cluster of identical files).
- **`utils.py`**
  Pure helper functions. Handling SHA-256 local hashing (`sha256`), checking safety (`is_protected_path`), formatting text (`fmt_size`), opening contexts, and auto-detecting thread counts (`optimal_workers`). 

### 3. `features/scanner/` (Duplicate Finder)
- **`worker.py`**
  Contains `ScanWorker` (runs on a `QThread`). It traverses directories, groups by file size, drops unique sizes, assigns tasks to a `ThreadPoolExecutor` to hash remaining files in parallel, and emits final `DuplicateGroup`s.
- **`tab.py`**
  Contains `ScanTab`. Constructs the `QTreeWidget` for viewing duplicate search results. Exposes UI components for `main_window.py` to populate.

### 4. `features/storage/` (Tree Size Analyzer)
- **`worker.py`**
  Contains `StorageWorker`. Recursively traverses the file system tree down to a specified depth (default 4) to sum up disk configurations without locking the UI.
- **`chart.py`**
  Contains `StorageChart` (a proportional, gradient-based horizontal bar chart built purely using `QPainter`) and `SizeBarDelegate` (a painter class that draws tiny proportional disk usage bars inside the `QTreeWidget` column).
- **`tab.py`**
  Contains `StorageTab`. Combines the horizontal chart and the detail tree into one cohesive View.

### 5. `features/ui/` (Shared Frontend)
Contains agnostic layout elements used globally across the app.
- **`header.py`**
  The `AppHeader` class. Provides the top visual banner mapping high-level progress (Total items scanned, reclaimable size, current status).
- **`sidebar.py`**
  The `Sidebar` class. Forms the fixed-width control rail housing the directory selection, minimum size spinbox, matching mode toggles, and "Move to Recycle Bin" actions.
- **`style.py`**
  The internal design system. Generates the custom `QPalette` dictating the dark theme background colours, text lightness, highlight accents, and provides a massive injected QSS syntax string unifying control stylings (like red danger buttons and green success text).

---

## Build & Deployment
- **`RedundantFileRemover.spec`**
  The PyInstaller configuration. Ensures `features` correctly compiles inward and explicitly targets `main.py`.
- **`build_exe.bat`**
  Developer script that runs PyInstaller in clean mode. 
- **`install.bat`** (Windows) / **`install.sh`** (Mac & Linux)
  User-facing installation scripts ensuring Python 3.10+ exists, downloading required dependencies (`Pip`, `PyQt6`, `send2trash`), and dropping desktop launcher shortcuts pointing directly to `main.py`.
