"""
features/scanner/tab.py
The "Duplicate Scanner" tab widget.
Enhanced with a 'Welcome' state for better production UX.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QTreeWidget, QHeaderView, QAbstractItemView,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class ScanTab(QWidget):
    """
    Duplicate-groups result view.
    Uses a StackedWidget to show a welcome screen before any scan.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(50)
        self.header_frame.setStyleSheet("background: transparent; border-bottom: 1px solid #21262d;")
        h_lay = QHBoxLayout(self.header_frame)
        h_lay.setContentsMargins(16, 0, 16, 0)

        heading = QLabel("DUPLICATE GROUPS")
        heading.setObjectName("sectionLabel")
        h_lay.addWidget(heading)
        h_lay.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#8b949e; font-size:11px; font-weight: 600;")
        h_lay.addWidget(self.count_lbl)
        self.main_lay.addWidget(self.header_frame)

        # ── Stack ─────────────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.main_lay.addWidget(self.stack)

        # 1. Welcome Page
        self.welcome_page = self._build_welcome()
        self.stack.addWidget(self.welcome_page)

        # 2. Results Page
        self.results_page = self._build_results()
        self.stack.addWidget(self.results_page)

    def _build_welcome(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(15)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 64px; color: #30363d;")
        lay.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Ready to sweep your storage?")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #e6edf3;")
        lay.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "Select a folder in the sidebar to begin.\n"
            "We'll find duplicate files using professional fingerprinting."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #8b949e; font-size: 14px; line-height: 1.4;")
        lay.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    def _build_results(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 12, 16, 16)
        
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
        self.dup_tree.setColumnWidth(1,  55)
        self.dup_tree.setColumnWidth(2,  80)
        self.dup_tree.setColumnWidth(3,  100)
        self.dup_tree.setColumnWidth(5,  180)

        lay.addWidget(self.dup_tree)
        return page

    def show_results(self, show: bool = True) -> None:
        self.stack.setCurrentIndex(1 if show else 0)
        self.header_frame.setVisible(show)
