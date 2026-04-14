"""
features/monitor/hash_index.py
In-memory hash index manager — no Qt imports allowed.
"""

from __future__ import annotations
from collections import defaultdict
import os

from features.core.utils import sha256, is_protected_path
from features.core.models import FileEntry, DuplicateGroup


class HashIndex:
    """
    Maintains two dicts:
        path  -> hash
        hash  -> [paths]
    """

    def __init__(self):
        self._path_to_hash: dict[str, str]       = {}
        self._hash_to_paths: dict[str, list[str]] = defaultdict(list)

    # ── public API ────────────────────────────────────────────

    def add(self, path: str) -> str | None:
        """Hash a file and add it to the index. Returns hash or None."""
        if is_protected_path(path):
            return None
        h = sha256(path)
        if not h:
            return None
        self._path_to_hash[path] = h
        if path not in self._hash_to_paths[h]:
            self._hash_to_paths[h].append(path)
        return h

    def remove(self, path: str) -> None:
        """Remove a file from the index."""
        h = self._path_to_hash.pop(path, None)
        if h:
            lst = self._hash_to_paths.get(h, [])
            if path in lst:
                lst.remove(path)
            if not lst:
                self._hash_to_paths.pop(h, None)

    def update(self, path: str) -> str | None:
        """Re-hash a modified file."""
        self.remove(path)
        return self.add(path)

    def get_duplicates(self) -> list[DuplicateGroup]:
        """Return groups where 2+ files share the same hash."""
        groups = []
        for gid, (h, paths) in enumerate(self._hash_to_paths.items()):
            if len(paths) < 2:
                continue
            entries = []
            for p in paths:
                try:
                    size = os.path.getsize(p)
                    name = os.path.basename(p)
                    entries.append(
                        FileEntry(
                            path=p,
                            name=name,
                            size=size,
                            hash_sha256=h,
                            protected=False,
                        )
                    )
                except OSError:
                    pass
            if len(entries) >= 2:
                groups.append(
                    DuplicateGroup(group_id=gid, files=entries, match_type="hash")
                )
        return groups

    def path_count(self) -> int:
        return len(self._path_to_hash)