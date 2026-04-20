"""
features/ui/style.py
Centralised stylesheet + application palette.
Redesigned for a premium, professional "production-ready" aesthetic.
"""

from PyQt6.QtGui import QColor, QPalette

STYLE = """
/* ── Global ── */
* {
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 14px;
}
QMainWindow, QWidget {
    background: #0d1117;
    color: #e6edf3;
}

/* ── Header bar ── */
#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #010409, stop:0.5 #0d1117, stop:1 #010409);
    border-bottom: 1px solid #30363d;
}
#titleLabel {
    color: #58a6ff;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
}
#subLabel {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
}

/* ── Stat chips in header ── */
#chip {
    background: rgba(22, 27, 34, 0.7);
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
}
#chip:hover {
    border-color: #58a6ff;
    background: #1c2128;
}
#chipVal {
    color: #58a6ff;
    font-size: 16px;
    font-weight: 800;
}
#chipKey {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

/* ── Tab bar ── */
QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 8px;
    background: #0d1117;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #8b949e;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 13px;
    min-width: 120px;
}
QTabBar::tab:selected {
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
    font-weight: 700;
}
QTabBar::tab:hover:!selected {
    color: #c9d1d9;
    background: rgba(48, 54, 61, 0.3);
    border-radius: 6px 6px 0 0;
}

/* ── Group boxes ── */
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 20px;
    color: #8b949e;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    background: #010409;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background: transparent;
}

/* ── Buttons ── */
QPushButton {
    background: #21262d;
    border: 1px solid #363b42;
    border-radius: 6px;
    padding: 8px 16px;
    color: #c9d1d9;
    font-weight: 600;
    font-size: 13px;
    min-height: 18px;
}
QPushButton:hover {
    background: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background: #161b22;
}
QPushButton:disabled {
    color: #484f58;
    border-color: #21262d;
    background: #0d1117;
}

QPushButton#primaryBtn {
    background: #238636;
    border: 1px solid rgba(240, 246, 252, 0.1);
    color: #ffffff;
}
QPushButton#primaryBtn:hover {
    background: #2ea043;
}
QPushButton#primaryBtn:pressed {
    background: #238636;
}

QPushButton#dangerBtn {
    background: #da3633;
    border: 1px solid rgba(240, 246, 252, 0.1);
    color: #ffffff;
}
QPushButton#dangerBtn:hover {
    background: #f85149;
}

#cloudButton {
    background-color: #2d7ff9;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px;
}

#cloudButton:hover {
    background-color: #1b5fd1;
}

/* ── Form Controls ── */
QLineEdit, QComboBox, QSpinBox {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e6edf3;
    selection-background-color: #1f6feb;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {
    border-color: #8b949e;
    background: #161b22;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #58a6ff;
    background: #0d1117;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #8b949e;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    outline: none;
}

/* ── Tree Widgets ── */
QTreeWidget {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    alternate-background-color: #161b22;
    color: #e6edf3;
    outline: none;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 8px;
    border-bottom: 1px solid #21262d;
}
QTreeWidget::item:selected {
    background: rgba(31, 111, 235, 0.15);
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
}
QTreeWidget::item:hover:!selected {
    background: #161b22;
}

QHeaderView::section {
    background: #161b22;
    border: none;
    border-right: 1px solid #30363d;
    border-bottom: 2px solid #30363d;
    padding: 10px;
    color: #8b949e;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 700;
}

/* ── Progress Bar ── */
QProgressBar {
    background: #21262d;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    height: 6px;
}
QProgressBar::chunk {
    background: #2f81f7;
    border-radius: 4px;
}

/* ── Status Bar ── */
QStatusBar {
    background: #010409;
    color: #8b949e;
    border-top: 1px solid #30363d;
    font-size: 12px;
}

/* ── Sidebar ── */
#sidebar {
    background: #010409;
    border-right: 1px solid #30363d;
}

/* ── Labels ── */
#pathLabel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px;
    color: #c9d1d9;
    font-size: 12px;
}
#sectionLabel {
    color: #e6edf3;
    font-size: 16px;
    font-weight: 700;
}
#statLabel {
    color: #8b949e;
    font-weight: 600;
}
#statGreen {
    color: #3fb950;
    font-weight: 700;
}
"""


def build_dark_palette() -> QPalette:
    pal = QPalette()
    C = QColor
    pal.setColor(QPalette.ColorRole.Window,          C("#0d1117"))
    pal.setColor(QPalette.ColorRole.WindowText,      C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Base,            C("#0d1117"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   C("#161b22"))
    pal.setColor(QPalette.ColorRole.Text,            C("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Button,          C("#21262d"))
    pal.setColor(QPalette.ColorRole.ButtonText,      C("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Highlight,       C("#1f6feb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, C("#ffffff"))
    return pal
