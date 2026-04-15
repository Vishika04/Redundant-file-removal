"""
features/ui/style.py
Centralised stylesheet + application palette.
Redesigned for clarity, readability, and layman-friendly UI.
"""

from PyQt6.QtGui import QColor, QPalette

STYLE = """
/* ── Global ── */
* {
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    font-size: 14px;
}
QMainWindow, QWidget {
    background: #0d1117;
    color: #e6edf3;
}

/* ── Header bar ── */
#header {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #010409, stop:0.5 #0d1529, stop:1 #0d1117);
    border-bottom: 2px solid #1f6feb;
}
#titleLabel {
    color: #58a6ff;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 3px;
}
#subLabel {
    color: #3d444d;
    font-size: 11px;
    letter-spacing: 2.5px;
}

/* ── Stat chips in header ── */
#chip {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 6px 16px;
}
#chip:hover {
    border-color: #58a6ff;
    background: #1c2128;
}
#chipVal {
    color: #58a6ff;
    font-size: 15px;
    font-weight: 800;
}
#chipKey {
    color: #8b949e;
    font-size: 12px;
    font-weight: 600;
}

/* ── Tab bar ── */
QTabWidget::pane {
    border: 1px solid #21262d;
    border-radius: 12px;
    background: #0d1117;
    top: -1px;
}
QTabBar::tab {
    background: #010409;
    color: #6e7681;
    padding: 12px 28px;
    border: none;
    border-bottom: 3px solid transparent;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.5px;
    min-width: 130px;
}
QTabBar::tab:selected {
    color: #58a6ff;
    border-bottom: 3px solid #1f6feb;
    background: #0d1117;
}
QTabBar::tab:hover:!selected {
    color: #c9d1d9;
    background: #0d1117;
}

/* ── Group boxes ── */
QGroupBox {
    border: 1px solid #21262d;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    color: #58a6ff;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    background: #010409;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    background: #010409;
}

/* ── Buttons — default ── */
QPushButton {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 9px 18px;
    color: #c9d1d9;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background: #1c2128;
    border-color: #58a6ff;
    color: #ffffff;
}
QPushButton:pressed {
    background: #010d1a;
    border-color: #1f6feb;
}
QPushButton:disabled {
    color: #3d444d;
    border-color: #21262d;
    background: #0d1117;
}

/* ── Primary (blue) button ── */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #2d7ff9, stop:1 #1f6feb);
    border: none;
    color: #ffffff;
    font-weight: 700;
    font-size: 14px;
    border-radius: 10px;
    padding: 10px 18px;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #4d94ff, stop:1 #2d7ff9);
}
QPushButton#primaryBtn:pressed {
    background: #1558cc;
}
QPushButton#primaryBtn:disabled {
    background: #1c2128;
    color: #3d444d;
}

/* ── Danger (red) button ── */
QPushButton#dangerBtn {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #e84040, stop:1 #da3633);
    border: none;
    color: #ffffff;
    font-weight: 700;
    font-size: 14px;
    border-radius: 10px;
    padding: 10px 18px;
}
QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ff5555, stop:1 #f85149);
}
QPushButton#dangerBtn:pressed {
    background: #b22120;
}
QPushButton#dangerBtn:disabled {
    background: #1c2128;
    color: #3d444d;
}

/* ── Stop button ── */
QPushButton#stopButton {
    background: #1c1400;
    border: 1px solid #9e6a03;
    color: #d29922;
    font-weight: 700;
    border-radius: 10px;
    padding: 9px 18px;
}
QPushButton#stopButton:hover {
    background: #2a1f00;
    border-color: #d29922;
    color: #e3b341;
}
QPushButton#stopButton:disabled {
    background: #0d1117;
    border-color: #21262d;
    color: #3d444d;
}

/* ── Form controls ── */
QLineEdit, QComboBox, QSpinBox {
    background: #010409;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e6edf3;
    font-size: 13px;
    selection-background-color: #1f6feb;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #58a6ff;
    background: #0d1117;
}
QLineEdit::placeholder {
    color: #484f58;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    color: #e6edf3;
    border-radius: 8px;
    padding: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border: none;
    background: #161b22;
    border-radius: 4px;
}

/* ── Tree widgets ── */
QTreeWidget {
    background: #010409;
    border: 1px solid #21262d;
    border-radius: 12px;
    alternate-background-color: #0a0f16;
    color: #e6edf3;
    outline: none;
    show-decoration-selected: 1;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 7px 6px;
    border-bottom: 1px solid #0d1117;
    min-height: 30px;
}
QTreeWidget::item:selected {
    background: #1f6feb;
    color: #ffffff;
    border-radius: 6px;
}
QTreeWidget::item:hover:!selected {
    background: #161b22;
    border-radius: 6px;
}
QTreeWidget::branch {
    background: #010409;
}

/* ── Table headers ── */
QHeaderView::section {
    background: #0d1117;
    border: none;
    border-right: 1px solid #21262d;
    border-bottom: 2px solid #21262d;
    padding: 10px 12px;
    color: #58a6ff;
    font-size: 12px;
    letter-spacing: 1px;
    font-weight: 700;
}

/* ── Progress bar ── */
QProgressBar {
    background: #010409;
    border: 1px solid #21262d;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    min-height: 22px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1f6feb, stop:1 #58a6ff);
    border-radius: 7px;
}

/* ── Stat labels ── */
QLabel#statLabel {
    color: #e3b341;
    font-size: 13px;
    font-weight: 700;
}
QLabel#statGreen {
    color: #3fb950;
    font-size: 13px;
    font-weight: 700;
}
QLabel#pathLabel {
    color: #8b949e;
    font-size: 12px;
    padding: 8px 12px;
    background: #010409;
    border: 1px solid #21262d;
    border-radius: 8px;
    min-height: 20px;
}
QLabel#warnLabel {
    color: #f0883e;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 12px;
    background: #1c1400;
    border: 1px solid #9e6a03;
    border-radius: 8px;
}
QLabel#sectionLabel {
    color: #58a6ff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
}

/* ── Status bar ── */
QStatusBar {
    background: #010409;
    color: #8b949e;
    border-top: 1px solid #21262d;
    font-size: 12px;
    padding: 4px 8px;
}

/* ── Scroll bars ── */
QScrollBar:vertical {
    background: #010409;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar:horizontal {
    background: #010409;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #58a6ff;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0; width: 0;
}
QScrollArea {
    border: none;
}

/* ── Checkboxes ── */
QCheckBox {
    color: #c9d1d9;
    spacing: 8px;
    font-size: 13px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #30363d;
    border-radius: 5px;
    background: #010409;
}
QCheckBox::indicator:checked {
    background: #1f6feb;
    border-color: #58a6ff;
}
QCheckBox::indicator:hover {
    border-color: #58a6ff;
}

/* ── Tooltips ── */
QToolTip {
    background: #161b22;
    color: #e6edf3;
    border: 1px solid #58a6ff;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ── Context menus ── */
QMenu {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    color: #e6edf3;
    padding: 6px;
    font-size: 13px;
}
QMenu::item {
    padding: 10px 24px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #1f6feb;
    color: #ffffff;
}
QMenu::separator {
    background: #21262d;
    height: 1px;
    margin: 6px 12px;
}

/* ── Sidebar ── */
#sidebar {
    background: #010409;
    border-right: 2px solid #21262d;
}

/* ── Message boxes ── */
QMessageBox {
    background: #161b22;
    color: #e6edf3;
    font-size: 14px;
}
QMessageBox QPushButton {
    min-width: 90px;
    min-height: 32px;
    font-size: 13px;
}
"""


def build_dark_palette() -> QPalette:
    """Return a QPalette that matches the dark stylesheet."""
    pal = QPalette()
    C = QColor
    pal.setColor(QPalette.ColorRole.Window,          C("#0d1117"))
    pal.setColor(QPalette.ColorRole.WindowText,      C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Base,            C("#010409"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   C("#0d1117"))
    pal.setColor(QPalette.ColorRole.Text,            C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Button,          C("#161b22"))
    pal.setColor(QPalette.ColorRole.ButtonText,      C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Highlight,       C("#1f6feb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, C("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     C("#161b22"))
    pal.setColor(QPalette.ColorRole.ToolTipText,     C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, C("#484f58"))
    return pal
