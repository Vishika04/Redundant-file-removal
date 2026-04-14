"""
features/similar/tab.py
The "Similar Files" tab widget - controls + results for perceptual media matching.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QHeaderView,
    QAbstractItemView, QPushButton, QSlider,
)
from PyQt6.QtCore import Qt


class SimilarTab(QWidget):
    """Similarity results and scan controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        heading_row = QHBoxLayout()
        heading = QLabel("SIMILAR FILES")
        heading.setObjectName("sectionLabel")
        heading_row.addWidget(heading)
        heading_row.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#484f58; font-size:11px;")
        heading_row.addWidget(self.count_lbl)
        lay.addLayout(heading_row)

        info = QLabel(
            "Perceptual image hashing (pHash + dHash) and audio fingerprints "
            "are compared against the selected similarity threshold."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#8b949e; font-size:11px; padding:4px 2px;")
        lay.addWidget(info)

        self._build_threshold_row(lay)
        self._build_buttons_row(lay)
        self._build_tree(lay)

    def _build_threshold_row(self, lay: QVBoxLayout) -> None:
        cap = QLabel("Similarity Threshold")
        cap.setStyleSheet("color:#6e7681; font-size:11px; margin-top:2px;")
        lay.addWidget(cap)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(70, 100)
        self.threshold_slider.setValue(90)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(5)
        row.addWidget(self.threshold_slider, stretch=1)

        self.threshold_value_lbl = QLabel("90%")
        self.threshold_value_lbl.setMinimumWidth(44)
        self.threshold_value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.threshold_value_lbl.setStyleSheet("color:#58a6ff; font-weight:700;")
        row.addWidget(self.threshold_value_lbl)

        lay.addLayout(row)

        self.threshold_hint = QLabel("Higher values mean stricter matching.")
        self.threshold_hint.setStyleSheet("color:#484f58; font-size:10px;")
        lay.addWidget(self.threshold_hint)

    def _build_buttons_row(self, lay: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(6)

        self.scan_btn = QPushButton("Start Similarity Scan")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setMinimumHeight(34)
        row.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(34)
        row.addWidget(self.stop_btn)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.select_btn = QPushButton("Select Close Matches")
        self.select_btn.setEnabled(False)
        self.select_btn.setMinimumHeight(32)
        row2.addWidget(self.select_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setEnabled(False)
        self.clear_btn.setMinimumHeight(32)
        row2.addWidget(self.clear_btn)
        lay.addLayout(row2)

        self.del_btn = QPushButton("Move Checked to Recycle Bin")
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setEnabled(False)
        self.del_btn.setMinimumHeight(36)
        lay.addWidget(self.del_btn)

    def _build_tree(self, lay: QVBoxLayout) -> None:
        self.sim_tree = QTreeWidget()
        self.sim_tree.setColumnCount(6)
        self.sim_tree.setHeaderLabels(
            ["  File Name", "Grp", "Type", "Similarity", "Size", "Path"]
        )
        self.sim_tree.setAlternatingRowColors(True)
        self.sim_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.sim_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sim_tree.setAnimated(True)
        self.sim_tree.setIndentation(20)
        self.sim_tree.setUniformRowHeights(True)

        hdr = self.sim_tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.sim_tree.setColumnWidth(1, 48)
        self.sim_tree.setColumnWidth(2, 72)
        self.sim_tree.setColumnWidth(3, 96)
        self.sim_tree.setColumnWidth(4, 92)

        lay.addWidget(self.sim_tree, stretch=1)

    def set_scan_running(self, running: bool) -> None:
        self.scan_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        if running:
            self.del_btn.setEnabled(False)
            self.select_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)

    def set_results_available(self, available: bool) -> None:
        self.del_btn.setEnabled(available)
        self.select_btn.setEnabled(available)
        self.clear_btn.setEnabled(available)

