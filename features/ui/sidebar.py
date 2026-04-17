"""
features/ui/sidebar.py
Left-hand control panel: directory picker, scan filters, scan control,
deletion actions, and live statistics.
Redesigned for a high-end production feel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox,
    QLabel, QPushButton, QComboBox, QSpinBox,
    QLineEdit, QCheckBox, QProgressBar, QHBoxLayout,
    QFrame
)
from PyQt6.QtCore import Qt


class Sidebar(QWidget):
    WIDTH = 320

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self.WIDTH)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("sidebar")
        scroll.setWidget(content)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 20, 16, 24)
        lay.setSpacing(20)

        # ── Directory Section ─────────────────────────────────────────────────
        lay.addWidget(self._build_directory_group())
        
        self.warn_label = QLabel("⚠ Protected system path — scan blocked.")
        self.warn_label.setObjectName("warnLabel")
        self.warn_label.setWordWrap(True)
        self.warn_label.hide()
        lay.addWidget(self.warn_label)

        # ── Filters & Options ─────────────────────────────────────────────────
        lay.addWidget(self._build_filters_group())

        # ── Actions ───────────────────────────────────────────────────────────
        lay.addWidget(self._build_actions_group())

        # ── Stats Dashboard ───────────────────────────────────────────────────
        lay.addWidget(self._build_stats_group())
        
        lay.addStretch()

    def _build_directory_group(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        lay.addWidget(_label("TARGET DIRECTORY"))
        self.path_label = QLabel("No folder selected")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_label.setMinimumHeight(44)
        lay.addWidget(self.path_label)

        self.browse_btn = QPushButton("📂  Select New Folder")
        self.browse_btn.setObjectName("primaryBtn")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setMinimumHeight(40)
        lay.addWidget(self.browse_btn)
        return container

    def _build_filters_group(self) -> QGroupBox:
        grp = _group("Options")
        lay = _vlay(grp, spacing=10)

        lay.addWidget(_cap("Comparison Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Smart Hash (SHA-256)", "Fast Name Match", "Safe Both"])
        lay.addWidget(self.mode_combo)

        lay.addWidget(_cap("Specific Extensions"))
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText("Leave blank for all...")
        lay.addWidget(self.ext_input)

        self.skip_sys_cb = QCheckBox("Protect System Files")
        self.skip_sys_cb.setChecked(True)
        lay.addWidget(self.skip_sys_cb)
        return grp

    def _build_actions_group(self) -> QGroupBox:
        grp = _group("Operations")
        lay = _vlay(grp, spacing=10)

        self.scan_btn = QPushButton("▶  Start Scan")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setMinimumHeight(38)
        lay.addWidget(self.scan_btn)
        
        # Tools Row
        row = QHBoxLayout()
        row.setSpacing(6)
        self.monitor_btn = QPushButton("👁  Monitor")
        self.monitor_btn.setToolTip("Watch for new duplicates in real-time")
        
        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setEnabled(False)
        
        row.addWidget(self.monitor_btn)
        row.addWidget(self.stop_btn)
        lay.addLayout(row)

        self.prog = QProgressBar()
        self.prog.setValue(0)
        lay.addWidget(self.prog)

        # Selection Helpers
        lay.addSpacing(4)
        self.auto_cb = QCheckBox("Auto-mark duplicates")
        lay.addWidget(self.auto_cb)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        self.sel_btn = QPushButton("Select All")
        self.clr_btn = QPushButton("Clear")
        self.sel_btn.setEnabled(False)
        self.clr_btn.setEnabled(False)
        row2.addWidget(self.sel_btn)
        row2.addWidget(self.clr_btn)
        lay.addLayout(row2)

        self.del_btn = QPushButton("🗑  Move to Trash")
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setEnabled(False)
        self.del_btn.setMinimumHeight(38)
        lay.addWidget(self.del_btn)
        return grp

    def _build_stats_group(self) -> QGroupBox:
        grp = _group("Performance Stats")
        lay = _vlay(grp, spacing=8)

        def _row(k: str, v_obj: str) -> QLabel:
            r = QHBoxLayout()
            key = QLabel(k)
            key.setStyleSheet("color:#6e7681; font-weight:600;")
            val = QLabel("—")
            val.setObjectName(v_obj)
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            r.addWidget(key)
            r.addWidget(val)
            lay.addLayout(r)
            return val

        self.s_groups  = _row("Groups Found", "statLabel")
        self.s_dupes   = _row("Duplicate Items", "statLabel")
        self.s_save    = _row("Reclaimable", "statGreen")
        self.s_scanned = _row("Total Scanned", "statLabel")
        self.s_prot    = _row("Protected Hits", "statLabel")
        return grp

    # ── Helpers ──
    def set_scan_running(self, running: bool) -> None:
        self.scan_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        if running:
            self.del_btn.setEnabled(False)
            self.sel_btn.setEnabled(False)
            self.clr_btn.setEnabled(False)

    def set_results_available(self, available: bool) -> None:
        self.del_btn.setEnabled(available)
        self.sel_btn.setEnabled(available)
        self.clr_btn.setEnabled(available)

    def reset_stats(self) -> None:
        for lbl in (self.s_groups, self.s_dupes, self.s_save, self.s_scanned, self.s_prot):
            lbl.setText("—")

    def match_mode(self) -> str:
        return ["hash", "name", "both"][self.mode_combo.currentIndex()]


def _group(title: str) -> QGroupBox:
    g = QGroupBox(title)
    return g

def _vlay(p, spacing=8) -> QVBoxLayout:
    l = QVBoxLayout(p)
    l.setContentsMargins(12, 22, 12, 14)
    l.setSpacing(spacing)
    return l

def _label(t) -> QLabel:
    l = QLabel(t)
    l.setStyleSheet("color:#8b949e; font-size:11px; font-weight:800; letter-spacing:1px;")
    return l

def _cap(t) -> QLabel:
    l = QLabel(t)
    l.setStyleSheet("color:#6e7681; font-size:11px; font-weight:600;")
    return l
