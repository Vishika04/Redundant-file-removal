"""
features/monitor/tab.py
View-only tab for Live Monitor — no business logic here.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem, QPushButton,
)
from PyQt6.QtCore import QTime, Qt
from PyQt6.QtGui  import QColor, QBrush, QFont

from features.core.utils  import fmt_size
from features.core.models import DuplicateGroup


class MonitorTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Status row ────────────────────────────────────────
        status_row = QHBoxLayout()
        self.lbl_status  = QLabel("Idle — select a folder and click Start Monitor")
        self.lbl_indexed = QLabel("Indexed: 0 files")
        self.btn_stop    = QPushButton("⬛  Stop Monitor")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setObjectName("stopButton")

        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_indexed)
        status_row.addWidget(self.btn_stop)
        layout.addLayout(status_row)

        # ── Live event log ────────────────────────────────────
        layout.addWidget(self._section_label("Live File Events"))
        self.event_log = QTreeWidget()
        self.event_log.setHeaderLabels(["Event", "File Name", "Path", "Time"])
        self.event_log.setColumnWidth(0, 85)
        self.event_log.setColumnWidth(1, 200)
        self.event_log.setColumnWidth(2, 460)
        self.event_log.setColumnWidth(3, 80)
        self.event_log.setRootIsDecorated(False)
        layout.addWidget(self.event_log, stretch=1)

        # ── Duplicate alerts ──────────────────────────────────
        layout.addWidget(self._section_label("Duplicate Alerts (auto-detected on arrival)"))
        self.dupe_tree = QTreeWidget()
        self.dupe_tree.setHeaderLabels(["Hash (short)", "File Name", "Path", "Size"])
        self.dupe_tree.setColumnWidth(0, 120)
        self.dupe_tree.setColumnWidth(1, 200)
        self.dupe_tree.setColumnWidth(2, 360)
        self.dupe_tree.setColumnWidth(3, 80)
        layout.addWidget(self.dupe_tree, stretch=1)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        font = QFont(); font.setBold(True); font.setPointSize(10)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #58a6ff; margin-top: 4px;")
        return lbl

    # ── Called by MainWindow to push data in ──────────────────

    def set_status(self, text: str):
        self.lbl_status.setText("")

    def set_indexed_count(self, count: int):
        self.lbl_indexed.setText(f"Indexed: {count} files")

    def set_monitor_running(self, running: bool):
        self.btn_stop.setEnabled(running)
        status = "Monitoring…" if running else "Stopped."
        self.lbl_status.setText(status)

    def add_event(self, event_type: str, path: str):
        import os
        color_map = {
            "added":    "#3fb950",   # green
            "modified": "#d29922",   # orange
            "deleted":  "#f85149",   # red
        }
        item = QTreeWidgetItem([
            event_type.upper(),
            os.path.basename(path),
            path,
            QTime.currentTime().toString("hh:mm:ss"),
        ])
        item.setForeground(0, QBrush(QColor(color_map.get(event_type, "#c9d1d9"))))
        self.event_log.insertTopLevelItem(0, item)   # newest on top

        # Cap log at 500 rows to avoid memory bloat
        if self.event_log.topLevelItemCount() > 500:
            self.event_log.takeTopLevelItem(500)

    def show_duplicates(self, groups: list[DuplicateGroup]):
        self.dupe_tree.clear()
        for group in groups:
            root_item = QTreeWidgetItem([
                group.files[0].hash_sha256[:12] + "…" if group.files else "—",
                f"{len(group.files)} files",
                "",
                "",
            ])
            root_item.setForeground(0, QBrush(QColor("#58a6ff")))
            font = QFont(); font.setBold(True)
            root_item.setFont(0, font)

            for fe in group.files:
                child = QTreeWidgetItem([
                    "",
                    fe.name,
                    fe.path,
                    fmt_size(fe.size),
                ])
                root_item.addChild(child)

            self.dupe_tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)