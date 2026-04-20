"""
features/similar/tab.py
The "Similar Files" tab widget.
Redesigned for a professional, production-ready aesthetic.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QHeaderView,
    QAbstractItemView, QPushButton, QSlider, QFrame
)
from PyQt6.QtCore import Qt


class SimilarTab(QWidget):
    """Similarity results and scan controls."""

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

        heading = QLabel("SIMILAR MEDIA DETECTOR")
        heading.setObjectName("sectionLabel")
        h_lay.addWidget(heading)
        h_lay.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#8b949e; font-size:11px; font-weight: 600;")
        h_lay.addWidget(self.count_lbl)
        self.main_lay.addWidget(self.header_frame)

        # ── Content ───────────────────────────────────────────────────────────
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(12)
        
        # Info
        info = QLabel(
            "Detect perceptually similar images and audio using advanced fingerprinting "
            "comparisons. Adjust the threshold for stricter or looser matching."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#8b949e; font-size:12px;")
        lay.addWidget(info)

        # Controls Group
        ctrl = QFrame()
        ctrl.setStyleSheet("background: #161b22; border: 1px solid #30363d; border-radius: 8px;")
        ctrl_lay = QVBoxLayout(ctrl)
        ctrl_lay.setContentsMargins(12, 12, 12, 12)
        ctrl_lay.setSpacing(10)

        # Threshold
        t_lay = QHBoxLayout()
        cap = QLabel("Matching Sensitivity")
        cap.setStyleSheet("color:#c9d1d9; font-size:11px; font-weight:700;")
        t_lay.addWidget(cap)
        t_lay.addStretch()
        self.threshold_value_lbl = QLabel("90%")
        self.threshold_value_lbl.setStyleSheet("color:#58a6ff; font-weight:700;")
        t_lay.addWidget(self.threshold_value_lbl)
        ctrl_lay.addLayout(t_lay)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(70, 100)
        self.threshold_slider.setValue(90)
        ctrl_lay.addWidget(self.threshold_slider)

        # Buttons
        btn_lay = QHBoxLayout()
        self.scan_btn = QPushButton("Start Analysis")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setFixedHeight(34)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(34)
        
        btn_lay.addWidget(self.scan_btn, stretch=1)
        btn_lay.addWidget(self.stop_btn)
        ctrl_lay.addLayout(btn_lay)
        
        lay.addWidget(ctrl)

        # Action Row
        act_lay = QHBoxLayout()
        self.select_btn = QPushButton("Select Matches")
        self.select_btn.setEnabled(False)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setEnabled(False)
        self.del_btn = QPushButton("🗑 Delete Selected")
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setEnabled(False)
        
        act_lay.addWidget(self.select_btn)
        act_lay.addWidget(self.clear_btn)
        act_lay.addStretch()
        act_lay.addWidget(self.del_btn)
        lay.addLayout(act_lay)

        # Result Tree
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
        self.sim_tree.setColumnWidth(4, 95)
        
        lay.addWidget(self.sim_tree, stretch=1)
        self.main_lay.addWidget(content)

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
