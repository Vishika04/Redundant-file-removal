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
    Return a sensible hashing-thread count derived automatically from
    the machine's CPU core count. 2× cores, clamped between 4 and 16.
    The user never needs to see or set this.
    """
    cpus = os.cpu_count() or 4
    return min(max(cpus * 2, 4), 16)


def sha256(path: str) -> str:
    """Compute the SHA-256 digest of *path*; returns '' on read error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            while chunk := fh.read(1 << 20):   # 1 MiB chunks
                h.update(chunk)
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
