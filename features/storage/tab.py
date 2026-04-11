"""
features/storage/tab.py
The "Storage Tree View" tab widget — pure UI, no worker logic.

Exposes:
    stor_tree   QTreeWidget  — main tree
    depth_spin  QSpinBox     — depth selector
    load_btn    QPushButton  — triggers StorageWorker (signal wired externally)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTreeWidget, QHeaderView, QAbstractItemView,
    QPushButton, QSpinBox,
)
from PyQt6.QtCore import Qt


class StorageTab(QWidget):
    """Directory size-tree view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        # ── Section heading row ───────────────────────────────────────────────
        heading_row = QHBoxLayout()
        heading = QLabel("STORAGE TREE VIEW")
        heading.setObjectName("sectionLabel")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        depth_lbl = QLabel("Depth:")
        depth_lbl.setStyleSheet("color:#6e7681; font-size:11px;")
        heading_row.addWidget(depth_lbl)

        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 8)
        self.depth_spin.setValue(4)
        self.depth_spin.setSuffix(" levels")
        self.depth_spin.setFixedWidth(115)
        heading_row.addWidget(self.depth_spin)
        heading_row.addSpacing(8)

        self.load_btn = QPushButton("↺  Load Tree")
        self.load_btn.setFixedWidth(115)
        self.load_btn.setMinimumHeight(32)
        heading_row.addWidget(self.load_btn)
        lay.addLayout(heading_row)

        # ── Info banner ───────────────────────────────────────────────────────
        info = QLabel(
            "💡  Right-click any file or folder to open in Explorer or delete safely."
        )
        info.setStyleSheet("color:#484f58; font-size:11px; padding:4px 2px;")
        lay.addWidget(info)

        # ── Tree ──────────────────────────────────────────────────────────────
        self.stor_tree = QTreeWidget()
        self.stor_tree.setColumnCount(3)
        self.stor_tree.setHeaderLabels(["  Name", "Size", "Full Path"])
        self.stor_tree.setAlternatingRowColors(True)
        self.stor_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.stor_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stor_tree.setAnimated(True)
        self.stor_tree.setIndentation(22)
        self.stor_tree.setUniformRowHeights(True)

        hdr = self.stor_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.stor_tree.setColumnWidth(1, 105)

        lay.addWidget(self.stor_tree, stretch=1)
