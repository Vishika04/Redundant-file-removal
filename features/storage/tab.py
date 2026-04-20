"""
features/storage/tab.py
Storage Tree View tab.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
    QHeaderView, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt

from features.storage.chart import StorageChart, SizeBarDelegate


class StorageTab(QWidget):
    """Visual storage breakdown with tree and proportional bar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size_delegate = SizeBarDelegate()
        self._build()

    @property
    def size_delegate(self) -> SizeBarDelegate:
        return self._size_delegate

    def _build(self) -> None:
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: transparent; border-bottom: 1px solid #21262d;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        heading = QLabel("STORAGE VISUALIZATION")
        heading.setObjectName("sectionLabel")
        h_lay.addWidget(heading)
        h_lay.addStretch()
        self.main_lay.addWidget(header)

        # ── Content ───────────────────────────────────────────────────────────
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(12)

        # ── Chart ─────────────────────────────────────────────────────────────
        self.chart = StorageChart()
        lay.addWidget(self.chart)

        info = QLabel(
            "💡 Select chart segments to jump  ·  Right-click to manage files."
        )
        info.setStyleSheet("color:#8b949e; font-size:11px;")
        lay.addWidget(info)

        # ── Tree ──────────────────────────────────────────────────────────────
        self.stor_tree = QTreeWidget()
        self.stor_tree.setColumnCount(3)
        self.stor_tree.setHeaderLabels(["  Folder / File Name", "Usage Bar", "Full System Path"])
        self.stor_tree.setAlternatingRowColors(True)
        self.stor_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.stor_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stor_tree.setAnimated(True)
        self.stor_tree.setIndentation(22)
        self.stor_tree.setUniformRowHeights(True)

        self.stor_tree.setItemDelegateForColumn(1, self._size_delegate)

        hdr = self.stor_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.stor_tree.setColumnWidth(1, 160)

        lay.addWidget(self.stor_tree, stretch=1)
        self.main_lay.addWidget(content)
