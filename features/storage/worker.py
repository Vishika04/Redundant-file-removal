"""
features/storage/worker.py
Background worker that builds a recursive directory-size tree.
"""

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from features.core.utils import is_protected_path


class StorageWorker(QThread):
    """
    Emits:
        progress(int pct, str message)
        finished(dict)   — nested tree:  {name, path, size, is_dir, protected, children[]}
        error(str)
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, root: str, max_depth: int = 4) -> None:
        super().__init__()
        self.root      = root
        self.max_depth = max_depth
        self._abort    = False
        self._counter  = 0

    # ── public ────────────────────────────────────────────────────────────────

    def abort(self) -> None:
        self._abort = True

    # ── QThread.run ───────────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            self.progress.emit(2, "Building tree…")
            tree = self._build(Path(self.root), depth=0)
            self.progress.emit(100, "Done")
            self.finished.emit(tree)
        except Exception as exc:
            self.error.emit(str(exc))

    # ── private ───────────────────────────────────────────────────────────────

    def _build(self, p: Path, depth: int) -> dict:
        node: dict = {
            "name":      p.name or str(p),
            "path":      str(p),
            "is_dir":    p.is_dir(),
            "size":      0,
            "children":  [],
            "protected": is_protected_path(str(p)),
        }

        if p.is_file():
            try:
                node["size"] = p.stat().st_size
            except (OSError, PermissionError):
                pass
            return node

        if depth > self.max_depth:
            return node

        try:
            # dirs first, then files — both sorted alphabetically
            children = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            for child in children:
                if self._abort:
                    break
                self._counter += 1
                self.progress.emit(
                    min(95, self._counter % 96),
                    f"Reading {child.name}",
                )
                child_node = self._build(child, depth + 1)
                node["children"].append(child_node)
                node["size"] += child_node["size"]
        except (OSError, PermissionError):
            pass

        return node
