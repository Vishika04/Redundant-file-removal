"""
features/core/utils.py
Pure utility functions — no Qt dependency.
"""

import os

import hashlib
import subprocess
from pathlib import Path

from features.core.constants import PROTECTED_ROOTS, PROTECTED_EXTS, SKIP_DIR_NAMES, SYSTEM


# ── Path-safety checks ────────────────────────────────────────────────────────

def is_protected_path(path: str) -> bool:
    """Return True if *path* is inside a system-critical directory."""
    p = path.lower()
    if any(p.startswith(root) for root in PROTECTED_ROOTS if root):
        return True
    for part in Path(path).parts:
        if part.lower() in SKIP_DIR_NAMES:
            return True
    return False


def is_protected_file(path: str) -> bool:
    """Return True if *path* has a system-critical file extension."""
    return Path(path).suffix.lower() in PROTECTED_EXTS


def get_media_kind(path: str) -> str:
    """Categorize a file based on its extension for visualization purposes."""
    ext = Path(path).suffix.lower()
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.heic'):
        return "image"
    if ext in ('.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.opus', '.wma'):
        return "audio"
    if ext in ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'):
        return "video"
    if ext in ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf'):
        return "document"
    if ext in ('.txt', '.md', '.log', '.csv', '.json', '.xml', '.yaml'):
        return "text"
    if ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso', '.dmg'):
        return "archive"
    if ext in ('.exe', '.msi', '.bat', '.cmd', '.sh', '.bin', '.app'):
        return "app"
    if ext in ('.py', '.js', '.html', '.css', '.cpp', '.h', '.java', '.go', '.ts', '.jsx', '.tsx'):
        return "code"
    return "other"


# ── Human-readable size formatting ───────────────────────────────────────────

def fmt_size(b: float) -> str:
    """Convert a byte count to a compact, human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


# ── SHA-256 hashing ───────────────────────────────────────────────────────────

def optimal_workers() -> int:
    """
    Return a conservative hashing-thread count to ensure system stability.
    Uses ~50% of available cores, capped at 8, to prevent UI lag.
    """
    cpus = os.cpu_count() or 4
    # Leave half the cores for the OS and other apps
    return min(max(cpus // 2, 2), 8)


import time

def sha256(path: str) -> str:
    """
    Compute the SHA-256 digest of *path*.
    Includes a micro-yield to prevent pinning CPU cores during heavy IO.
    """
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            while chunk := fh.read(1 << 20):   # 1 MiB chunks
                h.update(chunk)
                time.sleep(0) # Yield to OS scheduler
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


# ── Shell integration ─────────────────────────────────────────────────────────

def open_in_explorer(path: str) -> None:
    """Reveal *path* in the OS file browser (non-blocking)."""
    try:
        p = Path(path)
        if SYSTEM == "Windows":
            flag = f'/select,"{path}"' if p.is_file() else f'"{path}"'
            subprocess.Popen(f"explorer {flag}")
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
    except Exception:
        pass
