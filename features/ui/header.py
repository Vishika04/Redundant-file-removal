"""
features/ui/header.py
Branded application header bar with live stat chips.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore    import Qt


class _Chip(QWidget):
    """A small key-value badge shown in the header."""

    def __init__(self, key: str, initial: str = "—") -> None:
        super().__init__()
        self.setObjectName("chip")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(6)

        lbl_key = QLabel(key + ":")
        lbl_key.setObjectName("chipKey")
        lay.addWidget(lbl_key)

        self._val = QLabel(initial)
        self._val.setObjectName("chipVal")
        lay.addWidget(self._val)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class AppHeader(QWidget):
    """
    Top header bar.
    Exposes three stat chips (c_groups, c_dupes, c_save) for external update.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(64)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(26, 0, 26, 0)
        lay.setSpacing(0)

        # Brand mark
        dot = QLabel("◈")
        dot.setStyleSheet("color:#1f6feb; font-size:26px;")
        lay.addWidget(dot)
        lay.addSpacing(12)

        # Title
        title = QLabel("REDUNDANT FILE REMOVER")
        title.setObjectName("titleLabel")
        lay.addWidget(title)
        lay.addSpacing(16)

        # Sub-tagline
        sub = QLabel("SCAN · DETECT · REMOVE SAFELY")
        sub.setObjectName("subLabel")
        lay.addWidget(sub)

        lay.addStretch()

        # Stat chips
        self.c_groups = _Chip("Groups")
        self.c_dupes  = _Chip("Dupes")
        self.c_save   = _Chip("Reclaimable")

        for chip in (self.c_groups, self.c_dupes, self.c_save):
            lay.addWidget(chip)
            lay.addSpacing(8)

    # ── convenience wrappers (match old _set_chip API) ────────────────────────

    def reset_chips(self) -> None:
        for chip in (self.c_groups, self.c_dupes, self.c_save):
            chip.set_value("—")
