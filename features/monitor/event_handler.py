"""
features/monitor/event_handler.py
Bridges watchdog OS callbacks into Qt signals.
No UI widgets touched here.
"""

from __future__ import annotations
import os

from watchdog.events import FileSystemEventHandler
from PyQt6.QtCore import QObject, pyqtSignal

from features.core.utils import is_protected_path


class MonitorEventHandler(QObject, FileSystemEventHandler):
    """
    Receives raw watchdog events.
    Emits Qt signals upward to MonitorWorker.
    """

    file_added    = pyqtSignal(str)
    file_modified = pyqtSignal(str)
    file_deleted  = pyqtSignal(str)

    def __init__(self, min_size: int = 0):
        QObject.__init__(self)
        FileSystemEventHandler.__init__(self)
        self._min_size = min_size

    def _should_process(self, path: str) -> bool:
        if is_protected_path(path):
            return False
        try:
            return os.path.isfile(path) and os.path.getsize(path) >= self._min_size
        except OSError:
            return False

    def on_created(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self.file_added.emit(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._should_process(event.src_path):
            self.file_modified.emit(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and not is_protected_path(event.src_path):
            self.file_deleted.emit(event.src_path)