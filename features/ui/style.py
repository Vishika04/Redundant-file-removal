"""
features/ui/style.py
Centralised stylesheet + application palette for the dark GitHub-inspired theme.
"""

from PyQt6.QtGui import QColor, QPalette

# ── Master QSS stylesheet ─────────────────────────────────────────────────────

STYLE = """
/* ── Global reset ── */
* { font-family: 'Segoe UI', 'Inter', Arial, sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #0d1117; color: #c9d1d9; }

/* ── Branded header bar ── */
#header { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
          stop:0 #010409, stop:0.6 #0a0f16, stop:1 #0d1117);
          border-bottom: 1px solid #21262d; }
#titleLabel { color: #58a6ff; font-size: 19px; font-weight: 700;
              letter-spacing: 2.5px; }
#subLabel   { color: #30363d; font-size: 10px; letter-spacing: 2px; }

/* ── Stat chips in header ── */
#chip    { background: #161b22; border: 1px solid #21262d;
           border-radius: 8px; padding: 4px 12px; }
#chipVal { color: #58a6ff; font-size: 12px; font-weight: 700; }
#chipKey { color: #484f58; font-size: 11px; }

/* ── Tab bar ── */
QTabWidget::pane { border: 1px solid #21262d; border-radius: 10px;
                   background: #0d1117; top: -1px; }
QTabBar::tab { background: #010409; color: #484f58; padding: 10px 26px;
               border: none; border-bottom: 2px solid transparent;
               font-weight: 600; font-size: 12px; letter-spacing: 0.5px; }
QTabBar::tab:selected { color: #58a6ff; border-bottom: 2px solid #1f6feb;
                        background: #0d1117; }
QTabBar::tab:hover:!selected { color: #8b949e; }

/* ── Group boxes ── */
QGroupBox { border: 1px solid #21262d; border-radius: 10px; margin-top: 12px;
            padding-top: 16px; color: #1f6feb; font-size: 10px;
            font-weight: 700; letter-spacing: 1.5px; background: #0d1117; }
QGroupBox::title { subcontrol-origin: margin; left: 14px;
                   padding: 0 6px; background: #0d1117; }

/* ── Buttons ── */
QPushButton { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
              padding: 7px 16px; color: #8b949e; font-weight: 500;
              }
QPushButton:hover   { background: #1c2128; border-color: #58a6ff; color: #c9d1d9; }
QPushButton:pressed { background: #010d1a; }
QPushButton:disabled { color: #21262d; border-color: #161b22; background: #0d1117; }

QPushButton#primaryBtn { background: #1f6feb; border: none; color: #fff;
                         font-weight: 600; border-radius: 8px; }
QPushButton#primaryBtn:hover { background: #388bfd; }
QPushButton#primaryBtn:pressed { background: #1558cc; }

QPushButton#dangerBtn  { background: #da3633; border: none; color: #fff;
                         font-weight: 600; border-radius: 8px; }
QPushButton#dangerBtn:hover  { background: #f85149; }
QPushButton#dangerBtn:pressed { background: #b22120; }

QPushButton#warnBtn    { background: #9e6a03; border: none; color: #fff;
                         font-weight: 600; border-radius: 8px; }
QPushButton#warnBtn:hover  { background: #d29922; color: #000; }

/* ── Form controls ── */
QLineEdit, QComboBox, QSpinBox {
    background: #010409; border: 1px solid #30363d; border-radius: 7px;
    padding: 6px 10px; color: #c9d1d9; selection-background-color: #1f6feb; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #58a6ff; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #161b22; border: 1px solid #30363d;
    selection-background-color: #1f6feb; color: #c9d1d9; border-radius: 6px; }
QSpinBox::up-button, QSpinBox::down-button { width: 18px; border: none;
    background: #161b22; }
QSpinBox::up-arrow   { image: none; color: #484f58; }
QSpinBox::down-arrow { image: none; color: #484f58; }

/* ── Tree widgets ── */
QTreeWidget { background: #010409; border: 1px solid #21262d; border-radius: 10px;
              alternate-background-color: #0d1117; color: #c9d1d9;
              outline: none; show-decoration-selected: 1; }
QTreeWidget::item { padding: 5px 4px; border-bottom: 1px solid #0d1117;
                    min-height: 28px; }
QTreeWidget::item:selected { background: #1f6feb; color: #fff; border-radius: 4px; }
QTreeWidget::item:hover:!selected { background: #161b22; }
QTreeWidget::branch { background: #010409; }
QTreeWidget::branch:has-siblings:!adjoins-item {
    border-left: 1px solid #30363d; margin-left: 6px; }
QTreeWidget::branch:has-siblings:adjoins-item {
    border-left: 1px solid #30363d;
    border-bottom: 1px solid #30363d; margin-left: 6px; }
QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
    border-bottom: 1px solid #30363d; margin-left: 6px; }

/* ── Table headers ── */
QHeaderView::section { background: #010409; border: none;
    border-right: 1px solid #21262d; border-bottom: 1px solid #21262d;
    padding: 9px 10px; color: #1f6feb;
    font-size: 10px; letter-spacing: 1px; font-weight: 700; }

/* ── Progress bar ── */
QProgressBar { background: #010409; border: 1px solid #21262d;
               border-radius: 7px; text-align: center;
               color: #58a6ff; font-size: 11px; min-height: 20px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 #1f6feb, stop:1 #388bfd); border-radius: 6px; }

/* ── Stat labels ── */
QLabel#statLabel { color: #e3b341; font-size: 12px; font-weight: 600; }
QLabel#statGreen { color: #3fb950; font-size: 12px; font-weight: 600; }
QLabel#pathLabel { color: #6e7681; font-size: 11px; padding: 7px 10px;
    background: #010409; border: 1px solid #21262d; border-radius: 7px; }
QLabel#warnLabel { color: #f0883e; font-size: 11px; padding: 7px 10px;
    background: #1c1400; border: 1px solid #9e6a03; border-radius: 7px; }
QLabel#sectionLabel { color: #1f6feb; font-size: 10px; font-weight: 700;
                      letter-spacing: 1.5px; }

/* ── Status bar ── */
QStatusBar { background: #010409; color: #484f58;
             border-top: 1px solid #21262d; font-size: 11px; padding: 2px 6px; }

/* ── Splitter handle ── */
QSplitter::handle { background: #21262d; width: 1px; }

/* ── Scroll bars ── */
QScrollBar:vertical   { background: #010409; width: 7px;  margin: 0; }
QScrollBar:horizontal { background: #010409; height: 7px; margin: 0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #30363d; border-radius: 4px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #1f6feb; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollArea { border: none; }

/* ── Checkboxes ── */
QCheckBox { color: #8b949e; spacing: 7px; }
QCheckBox::indicator { width: 16px; height: 16px;
    border: 1px solid #30363d; border-radius: 5px; background: #010409; }
QCheckBox::indicator:checked { background: #1f6feb; border-color: #58a6ff; }
QCheckBox::indicator:hover   { border-color: #58a6ff; }

/* ── Tooltips ── */
QToolTip { background: #161b22; color: #c9d1d9; border: 1px solid #58a6ff;
           border-radius: 5px; padding: 5px 9px; font-size: 11px; }

/* ── Context menus ── */
QMenu { background: #161b22; border: 1px solid #30363d;
        border-radius: 10px; color: #c9d1d9; padding: 5px; }
QMenu::item { padding: 9px 22px; border-radius: 6px; }
QMenu::item:selected { background: #1f6feb; color: #fff; }
QMenu::separator { background: #21262d; height: 1px; margin: 5px 10px; }

/* ── Sidebar ── */
#sidebar { background: #010409; border-right: 1px solid #21262d; }
"""


# ── Application-level dark palette ──────────────────────────────────────────

def build_dark_palette() -> QPalette:
    """Return a QPalette that matches the dark stylesheet."""
    pal = QPalette()
    C = QColor
    pal.setColor(QPalette.ColorRole.Window,          C("#0d1117"))
    pal.setColor(QPalette.ColorRole.WindowText,      C("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Base,            C("#010409"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   C("#0d1117"))
    pal.setColor(QPalette.ColorRole.Text,            C("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Button,          C("#161b22"))
    pal.setColor(QPalette.ColorRole.ButtonText,      C("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.Highlight,       C("#1f6feb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, C("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     C("#161b22"))
    pal.setColor(QPalette.ColorRole.ToolTipText,     C("#c9d1d9"))
    pal.setColor(QPalette.ColorRole.PlaceholderText, C("#484f58"))
    return pal
