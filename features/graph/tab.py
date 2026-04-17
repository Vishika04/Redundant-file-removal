"""
features/graph/tab.py
Media Analytics tab container.
Enhanced with Original/Duplicate detection and actionable context menus.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QMenu, QMessageBox
)
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QColor, QAction
from .view import BarChart, KIND_COLORS
from features.core.utils import fmt_size, open_in_explorer
import os

class GraphTab(QWidget):
    """Analytics dashboard with bar chart and actionable detail portal."""
    
    # Signal to notify main window that files were deleted
    files_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_groups = []
        self._all_similar = []
        self._selected_kind = ""
        self._build()

    def _build(self):
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: transparent; border-bottom: 1px solid #21262d;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        heading = QLabel("MEDIA ANALYTICS")
        heading.setObjectName("sectionLabel")
        h_lay.addWidget(heading)
        h_lay.addStretch()

        self.btn_refresh = QPushButton("🔄  Refresh Data")
        self.btn_refresh.setFixedWidth(130)
        h_lay.addWidget(self.btn_refresh)
        self.main_lay.addWidget(header)

        # ── Scroll Area for Dashboard ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: #0d1117;")
        
        container = QWidget()
        container.setStyleSheet("background: #0d1117;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(24)

        # 1. Chart Card
        chart_card = QFrame()
        chart_card.setMinimumHeight(450)
        chart_card.setStyleSheet("background: #161b22; border: 1px solid #30363d; border-radius: 12px;")
        chart_lay = QVBoxLayout(chart_card)
        chart_lay.setContentsMargins(20, 20, 20, 20)
        chart_lay.setSpacing(15)

        chart_title = QLabel("DISTRIBUTION BY MEDIA KIND")
        chart_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #8b949e; letter-spacing: 1.5px;")
        chart_lay.addWidget(chart_title)

        self.chart = BarChart()
        chart_lay.addWidget(self.chart)
        
        chart_hint = QLabel("💡 Click any bar to drill down into file-level details.")
        chart_hint.setStyleSheet("color: #484f58; font-size: 11px; border: none;")
        chart_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_lay.addWidget(chart_hint)

        lay.addWidget(chart_card)

        # 2. Detailed List Card
        self.details_card = QFrame()
        self.details_card.setMinimumHeight(500)
        self.details_card.setStyleSheet("background: #161b22; border: 1px solid #30363d; border-radius: 12px;")
        details_lay = QVBoxLayout(self.details_card)
        details_lay.setContentsMargins(20, 20, 20, 20)
        details_lay.setSpacing(15)
        
        self.details_title = QLabel("INDEXED CONTENT DETAILS")
        self.details_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #8b949e; letter-spacing: 1.5px;")
        details_lay.addWidget(self.details_title)
        
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["File Name", "Role", "Group", "Size", "Full Path"])
        self.tree.setStyleSheet("""
            QTreeWidget { border: none; background: transparent; selection-background-color: #1f6feb30; outline: none; }
            QHeaderView::section { background: #0d1117; color: #8b949e; border: none; padding: 6px; font-weight: bold; border-bottom: 1px solid #30363d; }
        """)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        hdr = self.tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 80)
        self.tree.setColumnWidth(3, 100)
        
        details_lay.addWidget(self.tree)
        
        lay.addWidget(self.details_card)
        lay.addStretch()

        scroll.setWidget(container)
        self.main_lay.addWidget(scroll)

        # Interaction
        self.chart.category_selected.connect(self._on_category_selected)

    def set_data(self, duplicate_groups, similar_groups=None, all_indexed=None):
        self._all_groups = duplicate_groups or []
        self._all_similar = similar_groups or []
        self._all_indexed = all_indexed or []
        
        counts = {}
        # If we have all indexed files from the scanner, use them (includes unique nested files)
        # Otherwise fall back to just groups
        if self._all_indexed:
            all_files = self._all_indexed
        else:
            all_files = []
            for g in self._all_groups: all_files.extend(g.files)
            for sg in self._all_similar: all_files.extend(sg.files)
        
        for f in all_files:
            k = f.media_kind or "other"
            counts[k] = counts.get(k, 0) + 1
        
        self.chart.set_data(counts)
        self.tree.clear()
        if not self._selected_kind:
            self.details_title.setText("INDEXED CONTENT DETAILS (SELECT CATEGORY ABOVE)")
        else:
            self._on_category_selected(self._selected_kind)

    def _on_category_selected(self, kind: str):
        self._selected_kind = kind
        self.tree.clear()
        if not kind:
            self.details_title.setText("INDEXED CONTENT DETAILS")
            return
            
        self.details_title.setText(f"DETAILED LIST: {kind.upper()}S (RIGHT-CLICK TO MANAGE)")
        
        # 1. First, map files that ARE in groups for "Original/Duplicate" roles
        grouped_paths = set()
        
        for idx, g in enumerate(self._all_groups):
            for i, f in enumerate(g.files):
                if f.media_kind == kind:
                    self._add_tree_item(f, "Original" if i == 0 else "Duplicate", f"G-{idx}")
                    grouped_paths.add(f.path)
                    
        for idx, sg in enumerate(self._all_similar):
            for i, f in enumerate(sg.files):
                if f.media_kind == kind:
                    self._add_tree_item(f, "Original" if i == 0 else "Similar", f"S-{idx}")
                    grouped_paths.add(f.path)

        # 2. Then, add all OTHER indexed files as "Unique"
        for f in self._all_indexed:
            if f.media_kind == kind and f.path not in grouped_paths:
                self._add_tree_item(f, "Unique", "None")

    def _add_tree_item(self, f, role, group_tag):
        item = QTreeWidgetItem(self.tree)
        item.setText(0, f.name)
        item.setText(1, role)
        item.setText(2, group_tag)
        item.setText(3, fmt_size(f.size))
        item.setText(4, f.path)
        
        # Visual cues
        color = QColor(KIND_COLORS.get(self._selected_kind, "#ffffff"))
        item.setForeground(0, color)
        
        if role == "Original":
            item.setBackground(1, QColor("#2ea04320")) # Light green tint
            item.setForeground(1, QColor("#3fb950"))
        elif role == "Unique":
            item.setForeground(1, QColor("#8b949e")) # Grey for unique
        else:
            item.setForeground(1, QColor("#f85149")) # Red for duplicates

        item.setData(0, Qt.ItemDataRole.UserRole, f)

    def _show_context_menu(self, pos):
        selection = self.tree.selectedItems()
        if not selection: return
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: #161b22; border: 1px solid #30363d; padding: 5px; }")
        
        # Actions for single selection
        if len(selection) == 1:
            item = selection[0]
            f = item.data(0, Qt.ItemDataRole.UserRole)
            
            act_reveal = QAction("📁  Reveal in Explorer", self)
            act_reveal.triggered.connect(lambda: open_in_explorer(f.path))
            menu.addAction(act_reveal)
            menu.addSeparator()

        # Actions for any selection
        act_delete = QAction(f"🗑️  Delete {len(selection)} Selected File(s)", self)
        act_delete.triggered.connect(self._delete_selected)
        menu.addAction(act_delete)
        
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _delete_selected(self):
        selection = self.tree.selectedItems()
        if not selection: return
        
        count = len(selection)
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to permanently delete {count} file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_paths = []
            for item in selection:
                f = item.data(0, Qt.ItemDataRole.UserRole)
                try:
                    if os.path.exists(f.path):
                        os.remove(f.path)
                    deleted_paths.append(f.path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete {f.name}:\n{str(e)}")
            
            if deleted_paths:
                self.files_deleted.emit()
                # Local refresh is handled by the signal round-trip to main window 
                # but we can also manually trigger a data request here if needed.
