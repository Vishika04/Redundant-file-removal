"""
features/core/constants.py
OS-level safety constants shared across the entire application.
"""

import os
import platform

SYSTEM = platform.system()

# ── Protected root paths ───────────────────────────────────────────────────────
PROTECTED_ROOTS: set[str] = set()

if SYSTEM == "Windows":
    _drive = os.environ.get("SystemDrive", "C:")
    PROTECTED_ROOTS = {
        f"{_drive}\\Windows",
        f"{_drive}\\Windows\\System32",
        f"{_drive}\\Program Files",
        f"{_drive}\\Program Files (x86)",
        f"{_drive}\\ProgramData",
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("WINDIR", ""),
    }
elif SYSTEM == "Darwin":
    PROTECTED_ROOTS = {"/System", "/Library", "/usr", "/bin", "/sbin", "/etc", "/private"}
else:
    PROTECTED_ROOTS = {"/bin", "/sbin", "/usr", "/lib", "/lib64", "/etc", "/proc", "/sys", "/dev"}

PROTECTED_ROOTS = {p.lower() for p in PROTECTED_ROOTS if p}

# ── Protected file extensions ──────────────────────────────────────────────────
PROTECTED_EXTS: frozenset[str] = frozenset({
    ".exe", ".dll", ".sys", ".drv", ".inf", ".cat", ".mui",
    ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".reg",
    ".dylib", ".kext", ".so", ".ko",
})

# ── Directory names to skip during traversal ──────────────────────────────────
SKIP_DIR_NAMES: frozenset[str] = frozenset({
    "$recycle.bin", "system volume information", "windows",
    "program files", "program files (x86)", ".git", "__pycache__",
    "node_modules", ".svn", ".hg",
})

# ── Group accent colours for duplicate tree rows ──────────────────────────────
GROUP_COLORS: tuple[str, ...] = (
    "#1a3a5c", "#1a3a2e", "#3a1a2e", "#3a2e1a",
    "#2e1a3a", "#1a2e3a", "#3a1a1a", "#1e2a18",
)
