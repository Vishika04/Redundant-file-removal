"""
features/ui/sidebar.py
Left-hand control panel: directory picker, scan filters, scan control,
deletion actions, and live statistics.

Exposes all interactive widgets as public attributes so the main window
can wire signals/slots without reaching into private internals.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox,
    QLabel, QPushButton, QComboBox, QSpinBox,
    QLineEdit, QCheckBox, QProgressBar, QHBoxLayout,
)
from PyQt6.QtCore import Qt


class Sidebar(QWidget):
    """
    Fixed-width scrollable sidebar.

    Public attributes (widgets):
        path_label, warn_label, browse_btn
        mode_combo, min_spin, ext_input, skip_sys_cb
        scan_btn, stop_btn, prog
        auto_cb, sel_btn, clr_btn, del_btn
        s_groups, s_dupes, s_save, s_scanned, s_prot
    """

    WIDTH = 315

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(self.WIDTH)
        self._build()

    # ── construction ──────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("sidebar")
        scroll.setWidget(content)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(14, 18, 14, 18)
        lay.setSpacing(16)

        lay.addWidget(self._build_directory_group())
        self.warn_label = self._make_warn_label()
        lay.addWidget(self.warn_label)
        lay.addWidget(self._build_filters_group())
        lay.addWidget(self._build_scan_group())
        lay.addWidget(self._build_deletion_group())
        lay.addWidget(self._build_stats_group())
        lay.addStretch()

    # ── group builders ────────────────────────────────────────────────────────

    def _build_directory_group(self) -> QGroupBox:
        grp = _group("  DIRECTORY")
        lay = _vlay(grp, spacing=10)

        self.path_label = QLabel("No directory selected")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(38)
        lay.addWidget(self.path_label)

        self.browse_btn = QPushButton("📂  Browse Folder…")
        self.browse_btn.setObjectName("primaryBtn")
        self.browse_btn.setMinimumHeight(36)
        lay.addWidget(self.browse_btn)
        return grp

    def _make_warn_label(self) -> QLabel:
        lbl = QLabel("⚠  Protected / system path — scan blocked.")
        lbl.setObjectName("warnLabel")
        lbl.setWordWrap(True)
        lbl.hide()
        return lbl

    def _build_filters_group(self) -> QGroupBox:
        grp = _group("  SCAN FILTERS")
        lay = _vlay(grp, spacing=8)

        lay.addWidget(_cap("Match Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Content Hash (SHA-256)", "File Name Only", "Hash + Name"])
        self.mode_combo.setMinimumHeight(32)
        lay.addWidget(self.mode_combo)

        lay.addWidget(_cap("Minimum File Size"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 1_000_000)
        self.min_spin.setValue(1)
        self.min_spin.setSuffix(" KB")
        self.min_spin.setMinimumHeight(32)
        lay.addWidget(self.min_spin)

        lay.addWidget(_cap("Extensions  (blank = all)"))
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".jpg, .mp4, .pdf …")
        self.ext_input.setMinimumHeight(32)
        lay.addWidget(self.ext_input)

        self.skip_sys_cb = QCheckBox("Skip system / protected files")
        self.skip_sys_cb.setChecked(True)
        lay.addWidget(self.skip_sys_cb)
        return grp

    def _build_scan_group(self) -> QGroupBox:
        grp = _group("  SCAN")
        lay = _vlay(grp, spacing=8)

        self.scan_btn = QPushButton("▶  Start Scan")
        self.monitor_btn = QPushButton("👁  Start Monitor")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.setMinimumHeight(36)
        lay.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(36)
        lay.addWidget(self.stop_btn)

        self.prog = QProgressBar()
        self.prog.setValue(0)
        self.prog.setMinimumHeight(20)
        lay.addWidget(self.prog)
        return grp

    def _build_deletion_group(self) -> QGroupBox:
        grp = _group("  DELETION")
        lay = _vlay(grp, spacing=8)

        self.auto_cb = QCheckBox("Auto-select dupes  (keep oldest)")
        lay.addWidget(self.auto_cb)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.sel_btn = QPushButton("Select Dupes")
        self.sel_btn.setEnabled(False)
        self.sel_btn.setMinimumHeight(32)
        self.clr_btn = QPushButton("Clear All")
        self.clr_btn.setEnabled(False)
        self.clr_btn.setMinimumHeight(32)
        row.addWidget(self.sel_btn)
        row.addWidget(self.clr_btn)
        lay.addLayout(row)

        self.del_btn = QPushButton("🗑  Move to Recycle Bin")
        self.del_btn.setObjectName("dangerBtn")
        self.del_btn.setEnabled(False)
        self.del_btn.setMinimumHeight(36)
        lay.addWidget(self.del_btn)
        return grp

    def _build_stats_group(self) -> QGroupBox:
        grp = _group("  STATS")
        lay = _vlay(grp, spacing=7)

        def _stat(text: str, obj: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName(obj)
            lay.addWidget(lbl)
            return lbl

        self.s_groups  = _stat("Groups:              —", "statLabel")
        self.s_dupes   = _stat("Duplicates:          —", "statLabel")
        self.s_save    = _stat("Reclaimable:         —", "statGreen")
        self.s_scanned = _stat("Files in groups:     —", "statLabel")
        self.s_prot    = _stat("Protected (locked):  —", "statLabel")
        return grp

    # ── public helpers ─────────────────────────────────────────────────────────

    def set_scan_running(self, running: bool) -> None:
        """Toggle button / progress state during an active scan."""
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
            key = lbl.text().split(":")[0]
            lbl.setText(key + ": —")

    def match_mode(self) -> str:
        return ["hash", "name", "both"][self.mode_combo.currentIndex()]


# ── internal helpers ──────────────────────────────────────────────────────────

def _group(title: str) -> QGroupBox:
    return QGroupBox(title)


def _vlay(parent: QGroupBox, spacing: int = 8) -> QVBoxLayout:
    lay = QVBoxLayout(parent)
    lay.setContentsMargins(10, 20, 10, 14)
    lay.setSpacing(spacing)
    return lay


def _cap(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#6e7681; font-size:11px; margin-top:2px;")
    return lbl
