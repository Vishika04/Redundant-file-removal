"""
features/scanner/worker.py
Background worker that scans a directory for duplicate files.
"""

import os
import concurrent.futures
from collections import defaultdict
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from features.core.constants import SKIP_DIR_NAMES
from features.core.models import FileEntry, DuplicateGroup
from features.core.utils import is_protected_path, is_protected_file, sha256


class ScanWorker(QThread):
    """
    Emits:
        progress(int pct, str message)
        finished(list[DuplicateGroup])
        error(str)
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(
        self,
        root:       str,
        match_mode: str,        # "hash" | "name" | "both"
        min_size:   int,        # bytes
        ext_filter: str,        # comma-separated extensions, e.g. ".jpg,.png"
        workers:    int = 8,
    ) -> None:
        super().__init__()
        self.root       = root
        self.match_mode = match_mode
        self.min_size   = min_size
        self.ext_filter = [e.strip().lower() for e in ext_filter.split(",") if e.strip()]
        self.workers    = workers
        self._abort     = False

    # ── public ────────────────────────────────────────────────────────────────

    def abort(self) -> None:
        self._abort = True

    # ── private ───────────────────────────────────────────────────────────────

    def _accept(self, p: Path) -> bool:
        """Return True iff *p* passes all filters."""
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

    # ── QThread.run ───────────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            self._do_scan()
        except Exception as exc:
            self.error.emit(str(exc))

    def _do_scan(self) -> None:
        # ── 1. Collect file paths ─────────────────────────────────────────────
        self.progress.emit(2, "Collecting files…")
        all_files: list[Path] = []

        for dirpath, dirs, fnames in os.walk(self.root):
            if self._abort:
                return
            dirs[:] = [
                d for d in dirs
                if d.lower() not in SKIP_DIR_NAMES and not d.startswith("$")
            ]
            for fn in fnames:
                if self._abort:
                    return
                fp = Path(dirpath) / fn
                try:
                    if fp.is_file() and self._accept(fp):
                        all_files.append(fp)
                except (OSError, PermissionError):
                    pass

        if not all_files:
            self.finished.emit([])
            return

        # ── 2. Build FileEntry list ───────────────────────────────────────────
        total = len(all_files)
        self.progress.emit(5, f"{total} files found — building entries…")
        entries: list[FileEntry] = []

        for fp in all_files:
            if self._abort:
                return
            try:
                entries.append(FileEntry(
                    path=str(fp),
                    size=fp.stat().st_size,
                    name=fp.name,
                    extension=fp.suffix.lower(),
                    protected=is_protected_file(str(fp)),
                ))
            except (OSError, PermissionError):
                pass

        # ── 3. Hash files that share the same size (only when needed) ─────────
        if self.match_mode in ("hash", "both"):
            size_map: dict[int, list[FileEntry]] = defaultdict(list)
            for e in entries:
                size_map[e.size].append(e)

            to_hash = [e for grp in size_map.values() if len(grp) > 1 for e in grp]
            hash_total = len(to_hash)

            if hash_total:
                done = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
                    future_map = {pool.submit(sha256, e.path): e for e in to_hash}
                    for fut in concurrent.futures.as_completed(future_map):
                        if self._abort:
                            return
                        entry = future_map[fut]
                        done += 1
                        pct = 5 + int(done / hash_total * 70)
                        self.progress.emit(pct, f"Hashing: {entry.name}")
                        entry.hash_sha256 = fut.result()

        # ── 4. Build duplicate groups ─────────────────────────────────────────
        self.progress.emit(80, "Grouping duplicates…")
        groups: list[DuplicateGroup] = []
        gid = 0

        if self.match_mode in ("hash", "both"):
            buckets: dict[str, list[FileEntry]] = defaultdict(list)
            for e in entries:
                if e.hash_sha256:
                    buckets[e.hash_sha256].append(e)
            for members in buckets.values():
                if len(members) > 1:
                    g = DuplicateGroup(gid, files=members, match_type="hash")
                    for m in members:
                        m.group_id = gid
                    groups.append(g)
                    gid += 1

        if self.match_mode in ("name", "both"):
            name_map: dict[str, list[FileEntry]] = defaultdict(list)
            for e in entries:
                name_map[e.name.lower()].append(e)
            for members in name_map.values():
                if len(members) > 1:
                    ungrouped = [m for m in members if m.group_id == -1]
                    if len(ungrouped) > 1:
                        g = DuplicateGroup(gid, files=ungrouped, match_type="name")
                        for m in ungrouped:
                            m.group_id = gid
                        groups.append(g)
                        gid += 1

        self.progress.emit(100, f"Done — {len(groups)} group(s)")
        self.finished.emit(groups)
