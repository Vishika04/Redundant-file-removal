from PyQt6.QtCore import QThread, pyqtSignal
from collections import defaultdict

from features.core.models import FileEntry, DuplicateGroup
from features.scanner.cloud_scanner import fetch_drive_files

import traceback


class CloudWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            self._scan_cloud()
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))

    def _scan_cloud(self):
        self.progress.emit(5, "Fetching cloud files...")

        raw_files = fetch_drive_files()

        entries = []

        # convert to FileEntry
        for f in raw_files:
            entry = FileEntry(
                path=f["id"],
                size=f["size"],
                name=f["name"],
                extension="",
                protected=False,
                source="cloud"
            )

            entry.hash_md5 = f.get("hash")

            entries.append(entry)

        self.progress.emit(40, "Grouping duplicates...")

        # simple grouping (size + name)
        groups = []
        gid = 0

        size_map = defaultdict(list)
        for e in entries:
            size_map[e.size].append(e)

        for size_group in size_map.values():
            if len(size_group) < 2:
                continue

            # further grouping
            name_map = defaultdict(list)
            for e in size_group:
                name_map[e.name.lower()].append(e)

            for name_group in name_map.values():
                if len(name_group) < 2:
                    continue
                
                used_ids = set() 

                # check hash
                hash_map = defaultdict(list)
                for e in name_group:
                    if e.hash_md5:
                        hash_map[e.hash_md5].append(e)

                # HIGH confidence
                for h_group in hash_map.values():
                    if len(h_group) > 1:
                        for f in h_group:
                            f.confidence = "HIGH"
                            used_ids.add(f.path) # mark as used
                        g = DuplicateGroup(gid, files=h_group, match_type="hash")
                        groups.append(g)
                        gid += 1

                # MEDIUM confidence (no hash but name+size match)
                remaining = [e for e in name_group if e.path not in used_ids]
                if len(remaining) > 1:
                    for e in remaining:
                        e.confidence = "MEDIUM"
                    g = DuplicateGroup(gid, files=remaining, match_type="name")
                    groups.append(g)
                    gid += 1
        self.progress.emit(100, f"Done — {len(groups)} groups")
        self.finished.emit(groups)
    
    def abort(self):
        self._abort = True