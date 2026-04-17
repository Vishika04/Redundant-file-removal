"""
features/ui/header.py
Branded application header bar with live stat chips.
Redesigned for a high-end, production-ready aesthetic.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore    import Qt


class _Chip(QWidget):
    """A key-value stat badge shown in the header."""

    def __init__(self, key: str, initial: str = "—") -> None:
        super().__init__()
        self.setObjectName("chip")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(1)
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
        self.setFixedHeight(80)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(0)

        # Brand Section
        brand = QWidget()
        b_lay = QHBoxLayout(brand)
        b_lay.setContentsMargins(0, 0, 0, 0)
        
        logo = QLabel("◈")
        logo.setStyleSheet("color:#58a6ff; font-size:32px; font-weight:800;")
        b_lay.addWidget(logo)
        
        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        title_block.setContentsMargins(10, 0, 0, 0)
        
        title = QLabel("REDUCLEAR")
        title.setObjectName("titleLabel")
        title_block.addWidget(title)
        
        sub = QLabel("INTELLIGENT FILE MANAGEMENT")
        sub.setObjectName("subLabel")
        title_block.addWidget(sub)
        b_lay.addLayout(title_block)
        
        lay.addWidget(brand)
        lay.addStretch()

        # Stat chips
        chips_container = QWidget()
        c_lay = QHBoxLayout(chips_container)
        c_lay.setSpacing(12)
        
        self.c_groups = _Chip("Groups Found")
        self.c_dupes  = _Chip("Copies Found")
        self.c_save   = _Chip("Potential Saving")

        for chip in (self.c_groups, self.c_dupes, self.c_save):
            c_lay.addWidget(chip)
            
        lay.addWidget(chips_container)

    def reset_chips(self) -> None:
        for chip in (self.c_groups, self.c_dupes, self.c_save):
            chip.set_value("—")
