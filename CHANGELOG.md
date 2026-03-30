# Changelog

All notable changes to **Redundant File Remover** are documented here.

---

## v3.0 — 2026-03-27

### Added
- 🗂 **Storage Tree View tab** — browse folder structure as collapsible tree with recursive folder size rollups
- 🔒 **OS Safety Guards** — auto-blocks Windows system paths (`System32`, `Program Files`, `AppData`) and Unix paths (`/usr`, `/etc`, `/bin`)
- 🛡️ **Protected extension detection** — `.exe`, `.dll`, `.sys`, `.bat`, `.ps1` etc. flagged and deletion blocked
- ↺ **Recursive `StorageWorker`** — emits a nested dict tree instead of flat list; tree building is fully recursive and correct
- 📜 **Scrollable sidebar** — wrapped in `QScrollArea` so controls never clip on small screens
- 🖱️ **Context menu in both tabs** — Open in Explorer, check/uncheck, trash individual files
- 📦 **`install.bat` / `install.sh`** — one-click installers for Windows, macOS, and Linux
- 📦 **`build_exe.bat`** — automated PyInstaller build script

### Changed
- Sidebar widened from 275 → 310 px; all inputs now have `setMinimumHeight(30)` — nothing squashes
- `QGroupBox` internals use `setContentsMargins(10, 18, 10, 12)` for consistent breathing room
- Branch-line CSS added to `QTreeWidget` for proper visual tree connector lines
- Folder nodes rendered **Bold** for instant visual hierarchy

### Fixed
- Storage tree was rendering as a flat list — replaced with proper parent-child `QTreeWidgetItem` nesting
- `_build()` abort path now uses `break` instead of bare `return` to prevent `None` propagation

---

## v2.0 — 2026-03-27

### Added
- ⚡ Parallel SHA-256 hashing via `ThreadPoolExecutor`
- 🗑️ `send2trash` integration (always Recycle Bin, never permanent delete)
- 🎨 GitHub-inspired dark theme replacing original industrial theme
- Tab-switcher between Scanner and File Browser views
- Configurable thread count (1–32)
- Right-click context menus

### Changed
- Rewrote entire UI structure using `QTabWidget` instead of `QSplitter`
- Progress now emits real percentage during parallel hash phase

---

## v1.0 — Initial Release

- Basic duplicate scanner using MD5 + SHA-256
- `QTableWidget`-based results view
- Dark industrial stylesheet
- Auto-select duplicates (keep oldest)
- Send to Trash via `send2trash`
