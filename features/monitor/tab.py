"""
features/monitor/tab.py
The "Live Monitor" tab widget.
Redesigned for a professional, production-ready aesthetic.
"""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QFrame
)
from PyQt6.QtCore import QTime, Qt
from PyQt6.QtGui  import QColor, QBrush, QFont

from features.core.utils  import fmt_size
from features.core.models import DuplicateGroup


class MonitorTab(QWidget):
    """Real-time file system monitoring view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: transparent; border-bottom: 1px solid #21262d;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        heading = QLabel("LIVE STORAGE MONITOR")
        heading.setObjectName("sectionLabel")
        h_lay.addWidget(heading)
        h_lay.addStretch()

        self.btn_stop = QPushButton("■  Stop Monitoring")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setFixedHeight(30)
        h_lay.addWidget(self.btn_stop)
        self.main_lay.addWidget(header)

        # ── Content ───────────────────────────────────────────────────────────
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(10)

        # Status Banner
        self.status_banner = QFrame()
        self.status_banner.setStyleSheet("background: #161b22; border: 1px solid #30363d; border-radius: 6px;")
        sb_lay = QHBoxLayout(self.status_banner)
        sb_lay.setContentsMargins(15, 8, 15, 8)
        
        self.lbl_status = QLabel("Idle — Start from Sidebar")
        self.lbl_status.setStyleSheet("color: #8b949e; font-weight: 600;")
        self.lbl_indexed = QLabel("Indexed: 0 items")
        self.lbl_indexed.setStyleSheet("color: #58a6ff; font-weight: 700;")
        
        sb_lay.addWidget(self.lbl_status)
        sb_lay.addStretch()
        sb_lay.addWidget(self.lbl_indexed)
        lay.addWidget(self.status_banner)

        # Event Log
        lay.addWidget(self._section_label("REAL-TIME SYSTEM EVENTS"))
        self.event_log = QTreeWidget()
        self.event_log.setHeaderLabels(["Action", "File Name", "Location", "Timestamp"])
        self.event_log.setColumnWidth(0, 100)
        self.event_log.setColumnWidth(1, 180)
        self.event_log.setColumnWidth(2, 400)
        self.event_log.setRootIsDecorated(False)
        self.event_log.setAlternatingRowColors(True)
        lay.addWidget(self.event_log, stretch=3)

        # Duplicate Alerts
        lay.addWidget(self._section_label("AUTOMATIC DUPLICATE ALERTS"))
        self.dupe_tree = QTreeWidget()
        self.dupe_tree.setHeaderLabels(["Alert ID", "Occurrence", "Full Path", "File Size"])
        self.dupe_tree.setColumnWidth(0, 150)
        self.dupe_tree.setColumnWidth(1, 250)
        self.dupe_tree.setColumnWidth(2, 350)
        lay.addWidget(self.dupe_tree, stretch=2)

        self.main_lay.addWidget(content)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: 800; margin-top: 10px; letter-spacing: 0.5px;")
        return lbl

    def set_indexed_count(self, count: int):
        self.lbl_indexed.setText(f"Indexed: {count} items")

    def set_monitor_running(self, running: bool):
        self.btn_stop.setEnabled(running)
        status = "🟢  MONITORING ACTIVE" if running else "⚪  IDLE"
        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(f"color: {'#3fb950' if running else '#8b949e'}; font-weight: 800;")

    def add_event(self, event_type: str, path: str):
        import os
        color_map = {
            "added":    "#3fb950",
            "modified": "#d29922",
            "deleted":  "#f85149",
        }
        item = QTreeWidgetItem([
            event_type.upper(),
            os.path.basename(path),
            path,
            QTime.currentTime().toString("hh:mm:ss"),
        ])
        item.setForeground(0, QBrush(QColor(color_map.get(event_type, "#c9d1d9"))))
        font = QFont(); font.setBold(True)
        item.setFont(0, font)
        self.event_log.insertTopLevelItem(0, item)
        if self.event_log.topLevelItemCount() > 500:
            self.event_log.takeTopLevelItem(500)

    def show_duplicates(self, groups: list[DuplicateGroup]):
        self.dupe_tree.clear()
        for group in groups:
            root_item = QTreeWidgetItem([
                f"GRP-{group.group_id + 1}",
                f"{len(group.files)} occurrences detected",
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