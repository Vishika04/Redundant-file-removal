"""
main.py — Entry point for Redundant File Remover.

Run with:
    python main.py
or via the packaged executable built from RedundantFileRemover.spec.
"""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore    import Qt

from features.ui.style import build_dark_palette
from main_window       import MainWindow


import traceback

def global_exception_handler(exc_type, exc_value, exc_traceback):
    with open("crash.log", "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    print("CRASH LOGGED TO crash.log", file=sys.stderr)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def main() -> None:
    sys.excepthook = global_exception_handler
    app = QApplication(sys.argv)
    app.setApplicationName("Redundant File Remover")
    app.setApplicationVersion("3.1")
    app.setOrganizationName("RedundantFileRemover")
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
