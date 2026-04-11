"""
features/storage/tab.py
Storage Tree View tab — visual chart + detail tree.
Depth and Load controls are removed; loading is triggered automatically.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget,
    QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt

from features.storage.chart import StorageChart, SizeBarDelegate


class StorageTab(QWidget):
    """
    Layout:
        [section heading]
        [StorageChart  — proportional colour bar, 84 px]
        [info  banner]
        [QTreeWidget  — detail tree with size-bar delegate]
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size_delegate = SizeBarDelegate()
        self._build()

    @property
    def size_delegate(self) -> SizeBarDelegate:
        return self._size_delegate

    # ── construction ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        # Section heading
        heading = QLabel("STORAGE BREAKDOWN")
        heading.setObjectName("sectionLabel")
        lay.addWidget(heading)

        # ── Chart ─────────────────────────────────────────────────────────────
        self.chart = StorageChart()
        lay.addWidget(self.chart)

        # ── Tip banner ────────────────────────────────────────────────────────
        info = QLabel(
            "💡  Click any chart segment to jump to that folder  ·  "
            "Right-click a row to open in Explorer or delete safely."
        )
        info.setStyleSheet("color:#484f58; font-size:11px; padding:4px 2px;")
        lay.addWidget(info)

        # ── Detail tree ───────────────────────────────────────────────────────
        self.stor_tree = QTreeWidget()
        self.stor_tree.setColumnCount(3)
        self.stor_tree.setHeaderLabels(["  Name", "Size", "Full Path"])
        self.stor_tree.setAlternatingRowColors(True)
        self.stor_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.stor_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stor_tree.setAnimated(True)
        self.stor_tree.setIndentation(22)
        self.stor_tree.setUniformRowHeights(True)

        # Install the custom size-bar painter on column 1
        self.stor_tree.setItemDelegateForColumn(1, self._size_delegate)

        hdr = self.stor_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.stor_tree.setColumnWidth(1, 145)

        lay.addWidget(self.stor_tree, stretch=1)
