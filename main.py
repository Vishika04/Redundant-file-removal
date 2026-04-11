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


def main() -> None:
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
