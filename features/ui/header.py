"""
features/ui/header.py
Branded application header bar with live stat chips.
Redesigned for better visibility and layman-friendliness.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore    import Qt


class _Chip(QWidget):
    """A key-value stat badge shown in the header."""

    def __init__(self, key: str, initial: str = "—") -> None:
        super().__init__()
        self.setObjectName("chip")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 6, 14, 6)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._val = QLabel(initial)
        self._val.setObjectName("chipVal")
        self._val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._val)

        lbl_key = QLabel(key)
        lbl_key.setObjectName("chipKey")
        lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_key)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class AppHeader(QWidget):
    """
    Top header bar.
    Exposes three stat chips: c_groups, c_dupes, c_save.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(72)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(0)

        # Brand dot
        dot = QLabel("◈")
        dot.setStyleSheet("color:#1f6feb; font-size:28px;")
        lay.addWidget(dot)
        lay.addSpacing(14)

        # Title + tagline stacked
        title_block = QVBoxLayout()
        title_block.setSpacing(1)
        title_block.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("REDUNDANT FILE REMOVER")
        title.setObjectName("titleLabel")
        title_block.addWidget(title)

        sub = QLabel("SCAN  ·  DETECT  ·  REMOVE SAFELY")
        sub.setObjectName("subLabel")
        title_block.addWidget(sub)

        lay.addLayout(title_block)
        lay.addStretch()

        # Stat chips — with friendlier labels
        self.c_groups = _Chip("Duplicate Groups")
        self.c_dupes  = _Chip("Extra Copies Found")
        self.c_save   = _Chip("Space You Can Free")

        for chip in (self.c_groups, self.c_dupes, self.c_save):
            lay.addWidget(chip)
            lay.addSpacing(10)

    def reset_chips(self) -> None:
        for chip in (self.c_groups, self.c_dupes, self.c_save):
            chip.set_value("—")
