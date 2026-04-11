"""
╔══════════════════════════════════════════════════════════════════════╗
║  DEPRECATED — DO NOT RUN THIS FILE DIRECTLY                         ║
║                                                                      ║
║  This monolithic file has been refactored into the features/ package.║
║  The new entry point is:  main.py                                    ║
║                                                                      ║
║  Run:  python main.py                                                ║
║        (or double-click run.bat on Windows)                          ║
║                                                                      ║
║  This file is kept for historical reference only.                    ║
╚══════════════════════════════════════════════════════════════════════╝

Original: Redundant File Remover v3.0
Professional PyQt6 app — Duplicate Scanner + Storage Tree View
OS-safe: skips system/protected paths, always uses Recycle Bin
"""

import sys, os, hashlib, concurrent.futures, platform, subprocess, shutil
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from PyQt6.QtWidgets import QScrollArea
from typing import Optional

import send2trash
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QProgressBar, QSplitter, QCheckBox, QComboBox,
    QLineEdit, QGroupBox, QAbstractItemView, QMessageBox, QStatusBar,
    QSpinBox, QMenu, QTabWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette, QBrush, QAction, QIcon

# ── OS Safety ────────────────────────────────────────────────────────────────

SYSTEM = platform.system()

# Absolute forbidden paths — never scan or touch these
PROTECTED_ROOTS = set()
if SYSTEM == "Windows":
    sys_drive = os.environ.get("SystemDrive", "C:")
    PROTECTED_ROOTS = {
        f"{sys_drive}\\Windows",
        f"{sys_drive}\\Windows\\System32",
        f"{sys_drive}\\Program Files",
        f"{sys_drive}\\Program Files (x86)",
        f"{sys_drive}\\ProgramData",
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("WINDIR", ""),
    }
elif SYSTEM == "Darwin":
    PROTECTED_ROOTS = {"/System", "/Library", "/usr", "/bin", "/sbin", "/etc", "/private"}
else:
    PROTECTED_ROOTS = {"/bin", "/sbin", "/usr", "/lib", "/lib64", "/etc", "/proc", "/sys", "/dev"}

PROTECTED_ROOTS = {p.lower() for p in PROTECTED_ROOTS if p}

# File extensions that are OS-critical — never auto-mark these
PROTECTED_EXTS = {
    ".exe", ".dll", ".sys", ".drv", ".inf", ".cat", ".mui",
    ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".reg",
    ".dylib", ".kext", ".so", ".ko",
}

# Hidden / dot-prefixed directories to skip
SKIP_DIR_NAMES = {
    "$recycle.bin", "system volume information", "windows",
    "program files", "program files (x86)", ".git", "__pycache__",
    "node_modules", ".svn", ".hg",
}


def is_protected_path(path: str) -> bool:
    p = path.lower()
    if any(p.startswith(root) for root in PROTECTED_ROOTS if root):
        return True
    parts = Path(path).parts
    for part in parts:
        if part.lower() in SKIP_DIR_NAMES:
            return True
    return False


def is_protected_file(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in PROTECTED_EXTS


def fmt_size(b: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def open_in_explorer(path: str):
    try:
        p = Path(path)
        if SYSTEM == "Windows":
            if p.is_file():
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                subprocess.Popen(f'explorer "{path}"')
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
    except Exception:
        pass


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class FileEntry:
    path: str
    size: int
    name: str
    extension: str
    hash_sha256: str = ""
    group_id: int = -1
    protected: bool = False


@dataclass
class DuplicateGroup:
    group_id: int
    files: list = field(default_factory=list)
    match_type: str = "hash"


# ── Workers ───────────────────────────────────────────────────────────────────

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(1 << 20):
                h.update(chunk)
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


class ScanWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(self, root, match_mode, min_size, ext_filter, workers=8):
        super().__init__()
        self.root       = root
        self.match_mode = match_mode
        self.min_size   = min_size
        self.ext_filter = [e.strip().lower() for e in ext_filter.split(",") if e.strip()]
        self.workers    = workers
        self._abort     = False

    def abort(self): self._abort = True

    def _ok(self, p: Path) -> bool:
        try:
            if is_protected_path(str(p)):
                return False
            if p.stat().st_size < self.min_size:
                return False
            if self.ext_filter and p.suffix.lower() not in self.ext_filter:
                return False
        except (OSError, PermissionError):
            return False
        return True

    def run(self):
        try:
            self.progress.emit(2, "Collecting files…")
            all_files: list[Path] = []
            for dirpath, dirs, fnames in os.walk(self.root):
                if self._abort: return
                dirs[:] = [d for d in dirs
                           if d.lower() not in SKIP_DIR_NAMES
                           and not d.startswith('$')]
                for fn in fnames:
                    fp = Path(dirpath) / fn
                    try:
                        if fp.is_file() and self._ok(fp):
                            all_files.append(fp)
                    except (OSError, PermissionError):
                        pass
                    if self._abort: return

            if not all_files:
                self.finished.emit([])
                return

            total = len(all_files)
            self.progress.emit(5, f"{total} files found — grouping…")
            entries: list[FileEntry] = []

            for i, fp in enumerate(all_files):
                if self._abort: return
                try:
                    e = FileEntry(
                        path=str(fp), size=fp.stat().st_size,
                        name=fp.name, extension=fp.suffix.lower(),
                        protected=is_protected_file(str(fp))
                    )
                    entries.append(e)
                except (OSError, PermissionError):
                    pass

            if self.match_mode in ("hash", "both"):
                size_groups: dict[int, list] = defaultdict(list)
                for e in entries:
                    size_groups[e.size].append(e)
                
                to_hash = []
                for group in size_groups.values():
                    if len(group) > 1:
                        to_hash.extend(group)
                
                done = [0]
                hash_total = len(to_hash)
                
                if hash_total > 0:
                    futures = {}
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as ex:
                        for e in to_hash:
                            if self._abort: return
                            futures[ex.submit(_sha256, e.path)] = e
                            
                        for fut in concurrent.futures.as_completed(futures):
                            if self._abort: return
                            e = futures[fut]
                            done[0] += 1
                            pct = 5 + int(done[0] / hash_total * 70)
                            self.progress.emit(pct, f"Hashing: {e.name}")
                            e.hash_sha256 = fut.result()


            self.progress.emit(80, "Grouping duplicates…")
            groups: list[DuplicateGroup] = []
            gid = 0

            if self.match_mode in ("hash", "both"):
                buckets: dict[str, list] = defaultdict(list)
                for e in entries:
                    if e.hash_sha256:
                        buckets[e.hash_sha256].append(e)
                for members in buckets.values():
                    if len(members) > 1:
                        g = DuplicateGroup(gid, match_type="hash")
                        for m in members: m.group_id = gid
                        g.files = members
                        groups.append(g); gid += 1

            if self.match_mode in ("name", "both"):
                nb: dict[str, list] = defaultdict(list)
                for e in entries:
                    nb[e.name.lower()].append(e)
                for members in nb.values():
                    if len(members) > 1:
                        ug = [m for m in members if m.group_id == -1]
                        if len(ug) > 1:
                            g = DuplicateGroup(gid, match_type="name")
                            for m in ug: m.group_id = gid
                            g.files = ug
                            groups.append(g); gid += 1

            self.progress.emit(100, f"Done — {len(groups)} group(s)")
            self.finished.emit(groups)
        except Exception as exc:
            self.error.emit(str(exc))


class StorageWorker(QThread):
    """Emits a nested dict tree: {name, path, size, is_dir, children[]}"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)   # nested tree dict
    error    = pyqtSignal(str)

    def __init__(self, root, max_depth=4):
        super().__init__()
        self.root      = root
        self.max_depth = max_depth
        self._abort    = False

    def abort(self): self._abort = True

    def _dir_size(self, p: Path) -> int:
        total = 0
        try:
            for f in p.rglob("*"):
                if self._abort: return total
                try:
                    if f.is_file(): total += f.stat().st_size
                except (OSError, PermissionError): pass
        except (OSError, PermissionError): pass
        return total

    def _build(self, p: Path, depth: int, counter: list) -> dict:
        node = {"name": p.name, "path": str(p), "is_dir": p.is_dir(),
                "size": 0, "children": [], "protected": is_protected_path(str(p))}
        if p.is_file():
            try: node["size"] = p.stat().st_size
            except (OSError, PermissionError): pass
            return node
        if depth > self.max_depth:
            return node
        try:
            children = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for child in children:
                if self._abort:
                    break
                counter[0] += 1
                self.progress.emit(min(95, counter[0] % 96), f"Reading {child.name}")
                child_node = self._build(child, depth + 1, counter)
                node["children"].append(child_node)
                node["size"] += child_node["size"]
        except (OSError, PermissionError):
            pass
        return node

    def run(self):
        try:
            counter = [0]
            root_p = Path(self.root)
            self.progress.emit(2, "Building tree…")
            tree = self._build(root_p, 0, counter)
            self.progress.emit(100, "Done")
            self.finished.emit(tree)
        except Exception as exc:
            self.error.emit(str(exc))


# ── Stylesheet ────────────────────────────────────────────────────────────────

STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
QMainWindow, QWidget { background:#0d1117; color:#c9d1d9; }

#header { background:#010409; border-bottom:1px solid #21262d; }
#titleLabel { color:#58a6ff; font-size:18px; font-weight:700; letter-spacing:2px; }
#subLabel   { color:#30363d; font-size:10px; letter-spacing:2px; }
#chip       { background:#161b22; border:1px solid #21262d; border-radius:6px; padding:4px 10px; }
#chipVal    { color:#58a6ff; font-size:12px; font-weight:700; }
#chipKey    { color:#484f58; font-size:11px; }

QTabWidget::pane { border:1px solid #21262d; border-radius:8px; background:#0d1117; }
QTabBar::tab { background:#010409; color:#484f58; padding:10px 22px; border:none;
               border-bottom:2px solid transparent; font-weight:600; font-size:12px; }
QTabBar::tab:selected { color:#58a6ff; border-bottom:2px solid #1f6feb; background:#0d1117; }
QTabBar::tab:hover:!selected { color:#8b949e; }

QGroupBox { border:1px solid #21262d; border-radius:8px; margin-top:10px; padding-top:14px;
            color:#1f6feb; font-size:10px; font-weight:700; letter-spacing:1.5px;
            background:#0d1117; }
QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; background:#0d1117; }

QPushButton { background:#161b22; border:1px solid #30363d; border-radius:7px;
              padding:7px 16px; color:#8b949e; font-weight:500; }
QPushButton:hover { background:#1c2128; border-color:#58a6ff; color:#c9d1d9; }
QPushButton:pressed { background:#0d1117; }
QPushButton:disabled { color:#21262d; border-color:#161b22; }

QPushButton#primaryBtn { background:#1f6feb; border:none; color:#fff; font-weight:600; border-radius:7px; }
QPushButton#primaryBtn:hover { background:#388bfd; }
QPushButton#dangerBtn  { background:#da3633; border:none; color:#fff; font-weight:600; border-radius:7px; }
QPushButton#dangerBtn:hover { background:#f85149; }
QPushButton#warnBtn    { background:#9e6a03; border:none; color:#fff; font-weight:600; border-radius:7px; }
QPushButton#warnBtn:hover { background:#d29922; color:#000; }

QLineEdit, QComboBox, QSpinBox { background:#010409; border:1px solid #30363d; border-radius:6px;
    padding:6px 10px; color:#c9d1d9; selection-background-color:#1f6feb; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color:#58a6ff; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox QAbstractItemView { background:#161b22; border:1px solid #30363d;
    selection-background-color:#1f6feb; color:#c9d1d9; }

QTreeWidget { background:#010409; border:1px solid #21262d; border-radius:8px;
    alternate-background-color:#0d1117; color:#c9d1d9; outline:none; show-decoration-selected:1; }
QTreeWidget::item { padding:5px 4px; border-bottom:1px solid #0d1117; min-height:26px; }
QTreeWidget::item:selected { background:#1f6feb; color:#fff; }
QTreeWidget::item:hover:!selected { background:#161b22; }
QTreeWidget::branch {
    background: #010409;
}
QTreeWidget::branch:has-siblings:!adjoins-item {
    border-image: none;
    border-left: 1px solid #30363d;
    margin-left: 6px;
}
QTreeWidget::branch:has-siblings:adjoins-item {
    border-image: none;
    border-left: 1px solid #30363d;
    border-bottom: 1px solid #30363d;
    margin-left: 6px;
}
QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
    border-image: none;
    border-bottom: 1px solid #30363d;
    margin-left: 6px;
}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
    image: none;
    color: #58a6ff;
}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
    image: none;
}
QHeaderView::section { background:#010409; border:none; border-right:1px solid #21262d;
    border-bottom:1px solid #21262d; padding:8px 10px; color:#1f6feb;
    font-size:10px; letter-spacing:1px; font-weight:700; }

QProgressBar { background:#010409; border:1px solid #21262d; border-radius:6px;
    text-align:center; color:#58a6ff; font-size:11px; min-height:20px; }
QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 #1f6feb, stop:1 #388bfd); border-radius:5px; }

QLabel#statLabel { color:#e3b341; font-size:12px; font-weight:600; }
QLabel#statGreen  { color:#3fb950; font-size:12px; font-weight:600; }
QLabel#pathLabel  { color:#484f58; font-size:11px; padding:6px 10px;
    background:#010409; border:1px solid #21262d; border-radius:6px; }
QLabel#warnLabel  { color:#f0883e; font-size:11px; padding:6px 10px;
    background:#1c1400; border:1px solid #9e6a03; border-radius:6px; }

QStatusBar { background:#010409; color:#484f58; border-top:1px solid #21262d; font-size:11px; }
QSplitter::handle { background:#21262d; width:1px; }
QScrollBar:vertical { background:#010409; width:8px; }
QScrollBar::handle:vertical { background:#30363d; border-radius:4px; min-height:30px; }
QScrollBar::handle:vertical:hover { background:#1f6feb; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QCheckBox { color:#8b949e; spacing:6px; }
QCheckBox::indicator { width:16px; height:16px; border:1px solid #30363d;
    border-radius:4px; background:#010409; }
QCheckBox::indicator:checked { background:#1f6feb; border-color:#58a6ff; }
QToolTip { background:#161b22; color:#c9d1d9; border:1px solid #58a6ff;
    border-radius:4px; padding:4px 8px; font-size:11px; }

QMenu { background:#161b22; border:1px solid #30363d; border-radius:8px;
    color:#c9d1d9; padding:4px; }
QMenu::item { padding:8px 20px; border-radius:5px; }
QMenu::item:selected { background:#1f6feb; color:#fff; }
QMenu::separator { background:#21262d; height:1px; margin:4px 8px; }
"""

GROUP_COLORS = [
    "#1a3a5c", "#1a3a2e", "#3a1a2e", "#3a2e1a",
    "#2e1a3a", "#1a2e3a", "#3a1a1a", "#1e2a18",
]


# ── Main Window ───────────────────────────────────────────────────────────────

class RedundantFileRemover(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redundant File Remover  v3.0")
        self.setMinimumSize(1150, 720)
        self.resize(1380, 860)
        
        # Load Window Icon properly in PyInstaller environment
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'assets', 'logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self._scan_worker:    Optional[ScanWorker]    = None
        self._storage_worker: Optional[StorageWorker] = None
        self._groups:         list[DuplicateGroup]    = []
        self._selected_root  = ""
        self._build_ui()
        self.setStyleSheet(STYLE)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        c = QWidget(); self.setCentralWidget(c)
        root = QVBoxLayout(c); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        root.addWidget(self._make_header())

        body = QWidget(); bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)
        bl.addWidget(self._make_sidebar())

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._tabs.addTab(self._make_scan_tab(),    "⚡  Duplicate Scanner")
        self._tabs.addTab(self._make_storage_tab(), "🗂  Storage Tree View")
        bl.addWidget(self._tabs, stretch=1)

        body_wrap = QWidget(); bwl = QVBoxLayout(body_wrap)
        bwl.setContentsMargins(0, 0, 0, 0); bwl.setSpacing(0)
        bwl.addWidget(body)

        root.addWidget(body_wrap, stretch=1)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — select a folder to begin.")

    # Header
    def _make_header(self):
        h = QWidget(); h.setObjectName("header"); h.setFixedHeight(60)
        l = QHBoxLayout(h); l.setContentsMargins(24, 0, 24, 0)
        dot = QLabel("◈"); dot.setStyleSheet("color:#1f6feb;font-size:24px;"); l.addWidget(dot)
        l.addSpacing(10)
        tl = QLabel("REDUNDANT FILE REMOVER"); tl.setObjectName("titleLabel"); l.addWidget(tl)
        l.addSpacing(14)
        sl = QLabel("SCAN · DETECT · REMOVE SAFELY"); sl.setObjectName("subLabel"); l.addWidget(sl)
        l.addStretch()
        self._c_groups  = self._make_chip("Groups", "—")
        self._c_dupes   = self._make_chip("Dupes",  "—")
        self._c_save    = self._make_chip("Reclaimable", "—")
        for c in (self._c_groups, self._c_dupes, self._c_save):
            l.addWidget(c); l.addSpacing(8)
        return h

    def _make_chip(self, key, val):
        w = QWidget(); w.setObjectName("chip")
        l = QHBoxLayout(w); l.setContentsMargins(10, 4, 10, 4); l.setSpacing(6)
        k = QLabel(key + ":"); k.setObjectName("chipKey"); l.addWidget(k)
        v = QLabel(val);       v.setObjectName("chipVal"); l.addWidget(v)
        w._v = v; return w

    def _set_chip(self, chip, val): chip._v.setText(val)

    # Sidebar
    def _make_sidebar(self):
        # Outer shell (fixed width, dark bg, right border)
        outer = QWidget()
        outer.setFixedWidth(310)
        outer.setStyleSheet("background:#010409; border-right:1px solid #21262d;")
        outer_l = QVBoxLayout(outer)
        outer_l.setContentsMargins(0, 0, 0, 0)
        outer_l.setSpacing(0)

        # Scroll area so sidebar never clips content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none; background:#010409;}")
        outer_l.addWidget(scroll)

        s = QWidget()
        s.setStyleSheet("background:#010409;")
        scroll.setWidget(s)
        l = QVBoxLayout(s)
        l.setContentsMargins(14, 16, 14, 16)
        l.setSpacing(14)

        # ── Directory ──
        dg = QGroupBox("  DIRECTORY")
        dl = QVBoxLayout(dg); dl.setContentsMargins(10, 18, 10, 12); dl.setSpacing(10)
        self.path_label = QLabel("No directory selected")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(36)
        dl.addWidget(self.path_label)
        bb = QPushButton("📂  Browse Folder…")
        bb.setObjectName("primaryBtn"); bb.setMinimumHeight(34)
        bb.clicked.connect(self._browse)
        dl.addWidget(bb)
        l.addWidget(dg)

        self._warn_label = QLabel("⚠  Protected/system path — scan blocked.")
        self._warn_label.setObjectName("warnLabel")
        self._warn_label.setWordWrap(True)
        self._warn_label.hide()
        l.addWidget(self._warn_label)

        # ── Scan Filters ──
        fg = QGroupBox("  SCAN FILTERS")
        fl = QVBoxLayout(fg); fl.setContentsMargins(10, 18, 10, 12); fl.setSpacing(8)
        fl.addWidget(QLabel("Match Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Content Hash (SHA-256)", "File Name Only", "Hash + Name"])
        self.mode_combo.setMinimumHeight(30)
        fl.addWidget(self.mode_combo)
        fl.addWidget(QLabel("Minimum File Size"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 1_000_000)
        self.min_spin.setValue(1); self.min_spin.setSuffix(" KB")
        self.min_spin.setMinimumHeight(30)
        fl.addWidget(self.min_spin)
        fl.addWidget(QLabel("Extensions  (blank = all)"))
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".jpg, .mp4, .pdf …")
        self.ext_input.setMinimumHeight(30)
        fl.addWidget(self.ext_input)
        fl.addWidget(QLabel("Parallel Threads"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(8); self.workers_spin.setSuffix(" threads")
        self.workers_spin.setMinimumHeight(30)
        fl.addWidget(self.workers_spin)
        self.skip_sys_cb = QCheckBox("Skip system / protected files")
        self.skip_sys_cb.setChecked(True)
        fl.addWidget(self.skip_sys_cb)
        l.addWidget(fg)

        # ── Scan ──
        ag = QGroupBox("  SCAN")
        al = QVBoxLayout(ag); al.setContentsMargins(10, 18, 10, 12); al.setSpacing(8)
        self.scan_btn = QPushButton("▶  Start Scan")
        self.scan_btn.setObjectName("primaryBtn"); self.scan_btn.setMinimumHeight(34)
        self.scan_btn.clicked.connect(self._start_scan)
        al.addWidget(self.scan_btn)
        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setEnabled(False); self.stop_btn.setMinimumHeight(34)
        self.stop_btn.clicked.connect(self._abort)
        al.addWidget(self.stop_btn)
        self.prog = QProgressBar(); self.prog.setValue(0); self.prog.setMinimumHeight(20)
        al.addWidget(self.prog)
        l.addWidget(ag)

        # ── Deletion ──
        dg2 = QGroupBox("  DELETION")
        dl2 = QVBoxLayout(dg2); dl2.setContentsMargins(10, 18, 10, 12); dl2.setSpacing(8)
        self.auto_cb = QCheckBox("Auto-select dupes  (keep oldest)")
        dl2.addWidget(self.auto_cb)
        row = QHBoxLayout(); row.setSpacing(6)
        self.sel_btn = QPushButton("Select Dupes")
        self.sel_btn.setEnabled(False); self.sel_btn.setMinimumHeight(30)
        self.sel_btn.clicked.connect(self._select_dupes)
        self.clr_btn = QPushButton("Clear")
        self.clr_btn.setEnabled(False); self.clr_btn.setMinimumHeight(30)
        self.clr_btn.clicked.connect(self._clear_sel)
        row.addWidget(self.sel_btn); row.addWidget(self.clr_btn)
        dl2.addLayout(row)
        self.del_btn = QPushButton("🗑  Move to Recycle Bin")
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setEnabled(False); self.del_btn.setMinimumHeight(34)
        self.del_btn.clicked.connect(self._delete_checked)
        dl2.addWidget(self.del_btn)
        l.addWidget(dg2)

        # ── Stats ──
        sg = QGroupBox("  STATS")
        sl2 = QVBoxLayout(sg); sl2.setContentsMargins(10, 18, 10, 12); sl2.setSpacing(6)
        self.s_groups  = QLabel("Groups:             —"); self.s_groups.setObjectName("statLabel")
        self.s_dupes   = QLabel("Duplicates:         —"); self.s_dupes.setObjectName("statLabel")
        self.s_save    = QLabel("Reclaimable:        —"); self.s_save.setObjectName("statGreen")
        self.s_scanned = QLabel("Files in groups:    —"); self.s_scanned.setObjectName("statLabel")
        self.s_prot    = QLabel("Protected (locked): —"); self.s_prot.setObjectName("statLabel")
        for lbl in (self.s_groups, self.s_dupes, self.s_save, self.s_scanned, self.s_prot):
            sl2.addWidget(lbl)
        l.addWidget(sg)
        l.addStretch()
        return outer

    # ── Duplicate Scanner Tab ──────────────────────────────────────────────────

    def _make_scan_tab(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(14, 10, 14, 10); l.setSpacing(8)
        hr = QHBoxLayout()
        lbl = QLabel("DUPLICATE GROUPS"); lbl.setStyleSheet("color:#1f6feb;font-size:10px;font-weight:700;letter-spacing:1.5px;")
        hr.addWidget(lbl); hr.addStretch()
        self._count_lbl = QLabel(""); self._count_lbl.setStyleSheet("color:#484f58;font-size:11px;")
        hr.addWidget(self._count_lbl); l.addLayout(hr)

        self.dup_tree = QTreeWidget()
        self.dup_tree.setColumnCount(6)
        self.dup_tree.setHeaderLabels(["  File Name", "Grp", "Match", "Size", "Path", "SHA-256 (partial)"])
        self.dup_tree.setAlternatingRowColors(True)
        self.dup_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.dup_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dup_tree.customContextMenuRequested.connect(self._ctx_scan)
        self.dup_tree.setAnimated(True); self.dup_tree.setIndentation(18)
        hdr = self.dup_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.dup_tree.setColumnWidth(1, 44); self.dup_tree.setColumnWidth(2, 70)
        self.dup_tree.setColumnWidth(3, 88); self.dup_tree.setColumnWidth(5, 170)
        l.addWidget(self.dup_tree, stretch=1)
        return w

    # ── Storage Tree Tab ───────────────────────────────────────────────────────

    def _make_storage_tab(self):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(14, 10, 14, 10); l.setSpacing(8)
        hr = QHBoxLayout()
        lbl = QLabel("STORAGE TREE VIEW"); lbl.setStyleSheet("color:#1f6feb;font-size:10px;font-weight:700;letter-spacing:1.5px;")
        hr.addWidget(lbl); hr.addStretch()
        self._depth_spin = QSpinBox(); self._depth_spin.setRange(1, 8)
        self._depth_spin.setValue(4); self._depth_spin.setSuffix(" levels")
        self._depth_spin.setFixedWidth(110)
        reload_btn = QPushButton("↺  Load Tree"); reload_btn.setFixedWidth(110)
        reload_btn.clicked.connect(self._load_storage_tree)
        hr.addWidget(QLabel("Depth:")); hr.addWidget(self._depth_spin)
        hr.addSpacing(8); hr.addWidget(reload_btn)
        l.addLayout(hr)

        info = QLabel("💡  Right-click any file or folder to open in Explorer or delete safely.")
        info.setStyleSheet("color:#484f58;font-size:11px;padding:4px;")
        l.addWidget(info)

        self.stor_tree = QTreeWidget()
        self.stor_tree.setColumnCount(3)
        self.stor_tree.setHeaderLabels(["  Name", "Size", "Full Path"])
        self.stor_tree.setAlternatingRowColors(True)
        self.stor_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.stor_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stor_tree.customContextMenuRequested.connect(self._ctx_storage)
        self.stor_tree.setAnimated(True); self.stor_tree.setIndentation(20)
        hdr2 = self.stor_tree.header()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr2.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr2.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.stor_tree.setColumnWidth(1, 100)
        l.addWidget(self.stor_tree, stretch=1)
        return w

    # ── Slots: Browse & Scan ──────────────────────────────────────────────────

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder", str(Path.home()))
        if not d: return
        self._selected_root = d
        display = d if len(d) <= 36 else "…" + d[-34:]
        self.path_label.setText(display); self.path_label.setToolTip(d)
        if is_protected_path(d):
            self._warn_label.show()
            self.scan_btn.setEnabled(False)
            self.status_bar.showMessage(f"Directory: {d}")
        else:
            self._warn_label.hide()
            self.scan_btn.setEnabled(True)
            self.status_bar.showMessage(f"Directory: {d}")
            self._start_scan()

    def _mode(self):
        return ["hash", "name", "both"][self.mode_combo.currentIndex()]

    def _start_scan(self):
        if not self._selected_root:
            QMessageBox.warning(self, "No Folder", "Please select a folder first."); return
        if is_protected_path(self._selected_root):
            QMessageBox.critical(self, "Protected Path",
                "This path contains system files.\nChoose a user folder like Documents or Downloads.")
            return
        self.dup_tree.clear(); self._groups = []
        self.prog.setValue(0); self.scan_btn.setEnabled(False); self.stop_btn.setEnabled(True)
        self.del_btn.setEnabled(False); self.sel_btn.setEnabled(False); self.clr_btn.setEnabled(False)
        self._reset_stats()
        self._scan_worker = ScanWorker(
            self._selected_root, self._mode(),
            self.min_spin.value() * 1024,
            self.ext_input.text(),
            self.workers_spin.value()
        )
        self._scan_worker.progress.connect(self._on_prog)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.error.connect(self._on_error)
        self._scan_worker.start()
        self._tabs.setCurrentIndex(0)
        self.status_bar.showMessage("Scanning…")

    def _abort(self):
        if self._scan_worker: self._scan_worker.abort()
        if self._storage_worker: self._storage_worker.abort()
        self.stop_btn.setEnabled(False); self.scan_btn.setEnabled(True)
        self.status_bar.showMessage("Aborted.")

    def _on_prog(self, pct, msg):
        self.prog.setValue(pct)
        self.status_bar.showMessage(msg[:90] if len(msg) <= 90 else "…" + msg[-88:])

    def _on_scan_done(self, groups: list):
        self._groups = groups
        self.scan_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        if not groups:
            self.status_bar.showMessage("No duplicates found.")
            QMessageBox.information(self, "All Clear", "No duplicate files found."); return
        self._populate_dup_tree(groups)
        self._update_stats(groups)
        if self.auto_cb.isChecked(): self._select_dupes()
        self.sel_btn.setEnabled(True); self.clr_btn.setEnabled(True); self.del_btn.setEnabled(True)
        self.status_bar.showMessage(f"Done — {len(groups)} duplicate group(s) found.")

    def _on_error(self, msg):
        self.scan_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        QMessageBox.critical(self, "Error", msg)
        self.status_bar.showMessage("Error occurred.")

    # ── Populate duplicate tree ───────────────────────────────────────────────

    def _populate_dup_tree(self, groups: list[DuplicateGroup]):
        self.dup_tree.clear(); self.dup_tree.setSortingEnabled(False)
        total = 0
        for g in groups:
            col = QColor(GROUP_COLORS[g.group_id % len(GROUP_COLORS)])
            match_str = "HASH" if g.match_type == "hash" else "NAME"
            sz = sum(f.size for f in g.files)
            gh = QTreeWidgetItem()
            gh.setText(0, f"  ▸ Group {g.group_id + 1}  ·  {len(g.files)} files  ·  {match_str}")
            gh.setText(3, fmt_size(sz))
            for c in range(6): gh.setBackground(c, QBrush(col))
            gh.setForeground(0, QBrush(QColor("#58a6ff")))
            font = QFont(); font.setBold(True); font.setPointSize(11); gh.setFont(0, font)
            gh.setFlags(gh.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self.dup_tree.addTopLevelItem(gh)
            for i, fe in enumerate(g.files):
                ch = QTreeWidgetItem(gh)
                ch.setCheckState(0, Qt.CheckState.Unchecked)
                ch.setText(0, "    " + fe.name)
                ch.setText(1, f"G{g.group_id+1}"); ch.setText(2, match_str)
                ch.setText(3, fmt_size(fe.size)); ch.setText(4, fe.path)
                ch.setText(5, fe.hash_sha256[:22] + "…" if fe.hash_sha256 else "—")
                ch.setData(0, Qt.ItemDataRole.UserRole, fe)
                if i == 0:
                    ch.setForeground(0, QBrush(QColor("#3fb950")))
                    ch.setToolTip(0, "✓ Oldest copy — kept by auto-select")
                if fe.protected:
                    ch.setForeground(0, QBrush(QColor("#f0883e")))
                    ch.setToolTip(0, "⚠ Protected file extension — deletion blocked")
                total += 1
            gh.setExpanded(True)
        self.dup_tree.setSortingEnabled(True)
        self._count_lbl.setText(f"{len(groups)} groups · {total} files")

    # ── Storage Tree ──────────────────────────────────────────────────────────

    def _load_storage_tree(self):
        if not self._selected_root:
            QMessageBox.warning(self, "No Folder", "Select a folder first."); return
        self.stor_tree.clear()
        self.prog.setValue(0); self.scan_btn.setEnabled(False); self.stop_btn.setEnabled(True)
        self._storage_worker = StorageWorker(self._selected_root, self._depth_spin.value())
        self._storage_worker.progress.connect(self._on_prog)
        self._storage_worker.finished.connect(self._on_storage_done)
        self._storage_worker.error.connect(self._on_error)
        self._storage_worker.start()
        self._tabs.setCurrentIndex(1)

    def _on_storage_done(self, tree: dict):
        self.scan_btn.setEnabled(True); self.stop_btn.setEnabled(False); self.prog.setValue(100)
        self.stor_tree.clear()

        def make_item(parent_widget_or_item, node: dict) -> QTreeWidgetItem:
            is_dir  = node["is_dir"]
            prot    = node["protected"]
            name    = node["name"]
            size    = node["size"]
            path    = node["path"]

            if isinstance(parent_widget_or_item, QTreeWidget):
                item = QTreeWidgetItem()
                parent_widget_or_item.addTopLevelItem(item)
            else:
                item = QTreeWidgetItem(parent_widget_or_item)

            if is_dir:
                item.setText(0, "📁  " + name)
                item.setText(1, fmt_size(size) if size else "")
                item.setForeground(0, QBrush(QColor("#e3b341")))
                f = item.font(0); f.setBold(True); item.setFont(0, f)
            else:
                item.setText(0, "📄  " + name)
                item.setText(1, fmt_size(size))
                col = QColor("#f0883e") if prot else QColor("#8b949e")
                item.setForeground(0, QBrush(col))
                if prot:
                    item.setToolTip(0, "⚠  System/protected — deletion blocked")

            item.setText(2, path)
            item.setData(0, Qt.ItemDataRole.UserRole,
                         {"path": path, "is_dir": is_dir, "protected": prot})

            for child_node in node.get("children", []):
                make_item(item, child_node)

            if is_dir and node.get("children"):
                item.setExpanded(True)
            return item

        root_item = make_item(self.stor_tree, tree)
        root_item.setForeground(0, QBrush(QColor("#58a6ff")))
        f = root_item.font(0); f.setBold(True); f.setPointSize(12); root_item.setFont(0, f)
        root_item.setExpanded(True)
        self.status_bar.showMessage(f"Tree loaded: {self._selected_root}  |  {tree['size'] and fmt_size(tree['size']) or '—'}  total")

    # ── Context Menus ─────────────────────────────────────────────────────────

    def _ctx_scan(self, pos: QPoint):
        item = self.dup_tree.itemAt(pos)
        if not item or not item.parent(): return
        fe: FileEntry = item.data(0, Qt.ItemDataRole.UserRole)
        if not fe: return
        menu = QMenu(self)
        a_open   = menu.addAction("📂  Open in Explorer")
        menu.addSeparator()
        a_check  = menu.addAction("☑  Check (mark for deletion)")
        a_uncheck= menu.addAction("☐  Uncheck")
        menu.addSeparator()
        a_trash  = menu.addAction("🗑  Move THIS file to Recycle Bin")
        if fe.protected:
            a_trash.setEnabled(False);  a_trash.setText("🗑  Move to Recycle Bin  (BLOCKED — protected)")
        chosen = menu.exec(self.dup_tree.viewport().mapToGlobal(pos))
        if chosen == a_open:   open_in_explorer(fe.path)
        elif chosen == a_check:   item.setCheckState(0, Qt.CheckState.Checked)
        elif chosen == a_uncheck: item.setCheckState(0, Qt.CheckState.Unchecked)
        elif chosen == a_trash:   self._trash([fe.path])

    def _ctx_storage(self, pos: QPoint):
        items = self.stor_tree.selectedItems()
        if not items: return
        menu = QMenu(self)
        a_open  = menu.addAction("📂  Open in Explorer")
        menu.addSeparator()
        a_trash = menu.addAction(f"🗑  Move {len(items)} item(s) to Recycle Bin")
        chosen = menu.exec(self.stor_tree.viewport().mapToGlobal(pos))
        if chosen == a_open:
            data = items[0].data(0, Qt.ItemDataRole.UserRole)
            if data: open_in_explorer(data["path"])
        elif chosen == a_trash:
            protected = [it for it in items
                         if (it.data(0, Qt.ItemDataRole.UserRole) or {}).get("protected")]
            if protected:
                QMessageBox.warning(self, "Protected Items",
                    f"{len(protected)} item(s) are system/protected and were skipped.\n"
                    "Only user files will be moved.")
            paths = [it.data(0, Qt.ItemDataRole.UserRole)["path"] for it in items
                     if it.data(0, Qt.ItemDataRole.UserRole)
                     and not it.data(0, Qt.ItemDataRole.UserRole).get("protected")]
            self._trash(paths)

    # ── Deletion ──────────────────────────────────────────────────────────────

    def _trash(self, paths: list[str]):
        if not paths: return
        # Extra safety: never delete protected paths
        safe = [p for p in paths if not is_protected_path(p) and not is_protected_file(p)]
        blocked = len(paths) - len(safe)
        if not safe:
            QMessageBox.warning(self, "All Blocked",
                "All selected items are system/protected. Nothing was deleted."); return
        msg = f"Move {len(safe)} item(s) to the Recycle Bin?\n\nYou can restore them from the Recycle Bin."
        if blocked:
            msg += f"\n\n⚠  {blocked} protected item(s) were skipped automatically."
        reply = QMessageBox.question(self, "Confirm", msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        errors = []
        for p in safe:
            try:
                send2trash.send2trash(p)
            except Exception as e:
                errors.append(f"{Path(p).name}: {e}")
        if errors:
            QMessageBox.warning(self, "Some Errors", "\n".join(errors[:10]))
        ok = len(safe) - len(errors)
        self.status_bar.showMessage(f"✓ Moved {ok} item(s) to Recycle Bin.")
        QTimer.singleShot(500, self._start_scan)

    def _delete_checked(self):
        paths = []
        for i in range(self.dup_tree.topLevelItemCount()):
            p = self.dup_tree.topLevelItem(i)
            for j in range(p.childCount()):
                ch = p.child(j)
                if ch.checkState(0) == Qt.CheckState.Checked:
                    fe: FileEntry = ch.data(0, Qt.ItemDataRole.UserRole)
                    if fe and not fe.protected:
                        paths.append(fe.path)
        if not paths:
            QMessageBox.information(self, "Nothing Checked",
                "No (unprotected) files are checked."); return
        self._trash(paths)

    # ── Selection ─────────────────────────────────────────────────────────────

    def _select_dupes(self):
        """Check all but the first in each group (skip protected)."""
        for i in range(self.dup_tree.topLevelItemCount()):
            p = self.dup_tree.topLevelItem(i)
            for j in range(p.childCount()):
                ch = p.child(j)
                fe: FileEntry = ch.data(0, Qt.ItemDataRole.UserRole)
                if fe and fe.protected:
                    ch.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    ch.setCheckState(0, Qt.CheckState.Unchecked if j == 0 else Qt.CheckState.Checked)

    def _clear_sel(self):
        for i in range(self.dup_tree.topLevelItemCount()):
            p = self.dup_tree.topLevelItem(i)
            for j in range(p.childCount()):
                p.child(j).setCheckState(0, Qt.CheckState.Unchecked)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _update_stats(self, groups: list[DuplicateGroup]):
        dupes = sum(len(g.files) - 1 for g in groups)
        total = sum(len(g.files) for g in groups)
        save  = sum(sum(f.size for f in g.files[1:]) for g in groups)
        prot  = sum(1 for g in groups for f in g.files if f.protected)
        self.s_groups.setText(f"Groups:           {len(groups)}")
        self.s_dupes.setText(f"Duplicates:       {dupes}")
        self.s_save.setText(f"Reclaimable:      {fmt_size(save)}")
        self.s_scanned.setText(f"Files in groups:  {total}")
        self.s_prot.setText(f"Protected (locked): {prot}")
        self._set_chip(self._c_groups, str(len(groups)))
        self._set_chip(self._c_dupes, str(dupes))
        self._set_chip(self._c_save, fmt_size(save))

    def _reset_stats(self):
        for lbl in (self.s_groups, self.s_dupes, self.s_save, self.s_scanned, self.s_prot):
            t = lbl.text().split(":")[0]; lbl.setText(t + ": —")
        self._set_chip(self._c_groups, "—")
        self._set_chip(self._c_dupes, "—")
        self._set_chip(self._c_save, "—")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Redundant File Remover")
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#0d1117"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#010409"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#0d1117"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#161b22"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#1f6feb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)
    win = RedundantFileRemover()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
