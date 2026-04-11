"""
features/scanner/tab.py
The "Duplicate Scanner" tab widget — pure UI, no worker logic.

Exposes:
    dup_tree   QTreeWidget  — main result tree
    count_lbl  QLabel       — "N groups · M files" summary
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt


class ScanTab(QWidget):
    """Duplicate-groups result view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        # ── Section heading row ───────────────────────────────────────────────
        heading_row = QHBoxLayout()
        heading = QLabel("DUPLICATE GROUPS")
        heading.setObjectName("sectionLabel")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#484f58; font-size:11px;")
        heading_row.addWidget(self.count_lbl)
        lay.addLayout(heading_row)

        # ── Tree ──────────────────────────────────────────────────────────────
        self.dup_tree = QTreeWidget()
        self.dup_tree.setColumnCount(6)
        self.dup_tree.setHeaderLabels(
            ["  File Name", "Grp", "Match", "Size", "Path", "SHA-256 (partial)"]
        )
        self.dup_tree.setAlternatingRowColors(True)
        self.dup_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.dup_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.dup_tree.setAnimated(True)
        self.dup_tree.setIndentation(20)
        self.dup_tree.setUniformRowHeights(True)

        hdr = self.dup_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.dup_tree.setColumnWidth(1,  48)
        self.dup_tree.setColumnWidth(2,  72)
        self.dup_tree.setColumnWidth(3,  92)
        self.dup_tree.setColumnWidth(5, 175)

        lay.addWidget(self.dup_tree, stretch=1)
