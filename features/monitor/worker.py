"""
features/monitor/worker.py
QThread that owns the watchdog Observer and the HashIndex.
No UI widgets touched here.
"""

from __future__ import annotations
import os

from PyQt6.QtCore import QThread, pyqtSignal
from watchdog.observers import Observer

from features.monitor.hash_index    import HashIndex
from features.monitor.event_handler import MonitorEventHandler
from features.core.models           import DuplicateGroup


class MonitorWorker(QThread):

    # ── Signals → MainWindow listens to these ────────────────
    event_detected   = pyqtSignal(str, str)   # (event_type, path)
    duplicates_found = pyqtSignal(list)        # list[DuplicateGroup]
    index_updated    = pyqtSignal(int)         # total indexed file count
    error_occurred   = pyqtSignal(str)

    def __init__(self, folder: str, min_size: int = 0, parent=None):
        super().__init__(parent)
        self._folder   = folder
        self._min_size = min_size
        self._index    = HashIndex()
        self._observer = None
        self._handler  = None

    # ── Lifecycle ─────────────────────────────────────────────

    def run(self):
        try:
            self._build_initial_index()
            self._start_observer()
            self.exec()          # Qt event loop keeps thread alive
        except Exception as exc:
            self.error_occurred.emit(str(exc))

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
        self.quit()
        self.wait()

    # ── Initial full index ────────────────────────────────────

    def _build_initial_index(self):
        for root, _, files in os.walk(self._folder):
            for fname in files:
                path = os.path.join(root, fname)
                try:
                    if os.path.getsize(path) >= self._min_size:
                        self._index.add(path)
                except OSError:
                    pass
        self.index_updated.emit(self._index.path_count())

    # ── watchdog observer ─────────────────────────────────────

    def _start_observer(self):
        self._handler = MonitorEventHandler(min_size=self._min_size)
        self._handler.file_added.connect(self._on_added)
        self._handler.file_modified.connect(self._on_modified)
        self._handler.file_deleted.connect(self._on_deleted)

        self._observer = Observer()
        self._observer.schedule(self._handler, self._folder, recursive=True)
        self._observer.start()

    # ── Slots ─────────────────────────────────────────────────

    def _on_added(self, path: str):
        self._index.add(path)
        self.event_detected.emit("added", path)
        self.index_updated.emit(self._index.path_count())
        self._check_duplicates()

    def _on_modified(self, path: str):
        self._index.update(path)
        self.event_detected.emit("modified", path)
        self._check_duplicates()

    def _on_deleted(self, path: str):
        self._index.remove(path)
        self.event_detected.emit("deleted", path)
        self.index_updated.emit(self._index.path_count())

    def _check_duplicates(self):
        dupes = self._index.get_duplicates()
        if dupes:
            self.duplicates_found.emit(dupes)