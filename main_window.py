"""
main_window.py
Orchestrator: wires UI components to workers and business logic.
No raw Qt widget construction here — all UI built in feature modules.
"""

import os
import sys
from pathlib import Path
from typing import Callable, Optional

import send2trash
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMessageBox, QFileDialog, QMenu,
    QTreeWidgetItem, QTreeWidget,
)
from PyQt6.QtCore  import Qt, QPoint, QTimer
from PyQt6.QtGui   import QColor, QFont, QBrush, QIcon

from features.core.constants import GROUP_COLORS
from features.core.models    import DuplicateGroup, FileEntry
from features.core.utils     import (
    is_protected_path, is_protected_file,
    fmt_size, open_in_explorer, optimal_workers,
)
from features.scanner.worker  import ScanWorker
from features.scanner.tab     import ScanTab
from features.similar.worker  import SimilarityWorker
from features.similar.tab     import SimilarTab
from features.storage.worker  import StorageWorker
from features.storage.tab     import StorageTab
from features.storage.chart   import StorageChart
from features.ui.header       import AppHeader
from features.ui.sidebar      import Sidebar
from features.ui.style        import STYLE

_STORAGE_DEPTH = 4   # fixed tree depth, no user control needed


class MainWindow(QMainWindow):
    """Top-level window — pure orchestration, no widget building."""

    APP_VERSION = "v3.2"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Redundant File Remover  {self.APP_VERSION}")
        self.setMinimumSize(1150, 720)
        self.resize(1400, 880)
        self._load_icon()

        # ── State ─────────────────────────────────────────────────────────────
        self._scan_worker:       Optional[ScanWorker]    = None
        self._similar_worker:     Optional[SimilarityWorker] = None
        self._storage_worker:    Optional[StorageWorker] = None
        self._groups:            list[DuplicateGroup]    = []
        self._selected_root      = ""
        self._storage_loaded_for = ""   # track which root is currently shown

        # ── Build & style ──────────────────────────────────────────────────────
        self._build_ui()
        self.setStyleSheet(STYLE)

    # ── Icon ──────────────────────────────────────────────────────────────────

    def _load_icon(self) -> None:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base, "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_lay = QVBoxLayout(root_widget)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        self._header = AppHeader()
        root_lay.addWidget(self._header)

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self._sidebar = Sidebar()
        body_lay.addWidget(self._sidebar)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._scan_tab    = ScanTab()
        self._similar_tab = SimilarTab()
        self._storage_tab = StorageTab()
        self._tabs.addTab(self._scan_tab,    "⚡  Duplicate Scanner")
        self._tabs.addTab(self._similar_tab,  "◈  Similar Files")
        self._tabs.addTab(self._storage_tab, "🗂  Storage Breakdown")
        body_lay.addWidget(self._tabs, stretch=1)

        root_lay.addWidget(body, stretch=1)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — select a folder to begin.")

        self._wire_signals()

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        sb  = self._sidebar
        st  = self._scan_tab
        sim = self._similar_tab
        stt = self._storage_tab

        sb.browse_btn.clicked.connect(self._on_browse)
        sb.scan_btn.clicked.connect(self._start_scan)
        sb.stop_btn.clicked.connect(self._abort)
        sb.sel_btn.clicked.connect(self._select_dupes)
        sb.clr_btn.clicked.connect(self._clear_sel)
        sb.del_btn.clicked.connect(self._delete_checked)

        st.dup_tree.customContextMenuRequested.connect(self._ctx_scan)
        sim.threshold_slider.valueChanged.connect(self._on_similarity_threshold_changed)
        sim.scan_btn.clicked.connect(self._start_similarity_scan)
        sim.stop_btn.clicked.connect(self._abort)
        sim.select_btn.clicked.connect(self._select_similar_dupes)
        sim.clear_btn.clicked.connect(self._clear_similar_sel)
        sim.del_btn.clicked.connect(self._delete_checked_similar)
        sim.sim_tree.customContextMenuRequested.connect(self._ctx_similar)

        # Auto-load storage when the tab is activated
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Chart segment click → scroll + highlight tree row
        stt.chart.segment_clicked.connect(self._on_chart_segment_clicked)
        stt.stor_tree.customContextMenuRequested.connect(self._ctx_storage)

    # ── Tab switch ────────────────────────────────────────────────────────────

    def _on_tab_changed(self, index: int) -> None:
        """Auto-load storage tree when the storage tab becomes active."""
        if self._tabs.widget(index) is self._storage_tab and self._selected_root:
            if self._selected_root != self._storage_loaded_for:
                self._load_storage_tree()

    def _on_chart_segment_clicked(self, path: str) -> None:
        """Scroll the detail tree to the folder matching *path*."""
        tree = self._storage_tab.stor_tree
        for i in range(tree.topLevelItemCount()):
            top  = tree.topLevelItem(i)
            data = top.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("path") == path:
                tree.scrollToItem(top, QTreeWidget.ScrollHint.PositionAtTop)
                tree.setCurrentItem(top)
                break

    # ── Browse ────────────────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Folder", str(Path.home()))
        if not d:
            return
        self._selected_root  = d
        self._storage_loaded_for = ""      # force storage refresh

        # Clear stale storage view immediately
        self._scan_tab.dup_tree.clear()
        self._scan_tab.count_lbl.setText("")
        self._storage_tab.chart.clear()
        self._storage_tab.stor_tree.clear()
        self._sidebar.set_results_available(False)
        self._sidebar.reset_stats()
        self._header.reset_chips()
        self._similar_tab.sim_tree.clear()
        self._similar_tab.count_lbl.setText("")
        self._similar_tab.set_results_available(False)
        self._sync_tree_count(self._similar_tab.sim_tree, self._similar_tab.count_lbl)

        display = d if len(d) <= 38 else "…" + d[-36:]
        self._sidebar.path_label.setText(display)
        self._sidebar.path_label.setToolTip(d)

        if is_protected_path(d):
            self._sidebar.warn_label.show()
            self._sidebar.scan_btn.setEnabled(False)
            self._status.showMessage(f"Protected directory: {d}")
        else:
            self._sidebar.warn_label.hide()
            self._sidebar.scan_btn.setEnabled(True)
            self._status.showMessage(f"Directory: {d}")
            self._start_scan()

    # ── Scan ──────────────────────────────────────────────────────────────────

    def _start_scan(self) -> None:
        if not self._selected_root:
            QMessageBox.warning(self, "No Folder Selected",
                "Please click 'Browse Folder' to choose a folder first.")
            return
        if self._any_worker_running():
            QMessageBox.information(
                self,
                "Scan Already Running",
                "Please stop the current scan before starting another one.",
            )
            return
        if is_protected_path(self._selected_root):
            QMessageBox.critical(
                self, "This Folder is Protected",
                "You've selected a Windows system folder — scanning it could be harmful.\n\n"
                "Please choose a personal folder like Documents, Downloads, or Desktop.",
            )
            return

        self._scan_tab.dup_tree.clear()
        self._groups = []
        self._sidebar.prog.setValue(0)
        self._sidebar.set_scan_running(True)
        self._sidebar.reset_stats()
        self._header.reset_chips()

        sb = self._sidebar
        self._scan_worker = ScanWorker(
            root=self._selected_root,
            match_mode=sb.match_mode(),
            min_size=sb.min_spin.value() * 1024,
            ext_filter=sb.ext_input.text(),
            workers=optimal_workers(),
        )
        self._scan_worker.progress.connect(self._on_progress)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

        self._tabs.setCurrentIndex(0)
        self._status.showMessage("Scanning…")

    def _abort(self) -> None:
        if self._scan_worker:
            self._scan_worker.abort()
        if self._similar_worker:
            self._similar_worker.abort()
        if self._storage_worker:
            self._storage_worker.abort()
        self._sidebar.set_scan_running(False)
        self._sidebar.set_results_available(False)
        if hasattr(self, "_similar_tab"):
            self._similar_tab.set_scan_running(False)
            self._similar_tab.set_results_available(False)
        self._status.showMessage("Stopped.")

    # ── Progress ──────────────────────────────────────────────────────────────

    def _on_progress(self, pct: int, msg: str) -> None:
        self._sidebar.prog.setValue(pct)
        self._status.showMessage(msg if len(msg) <= 90 else "…" + msg[-88:])

    # ── Scan done ─────────────────────────────────────────────────────────────

    def _on_scan_done(self, groups: list) -> None:
        self._scan_worker = None
        self._groups = groups
        self._sidebar.set_scan_running(False)

        if not groups:
            self._status.showMessage("No duplicates found.")
            self._sidebar.set_results_available(False)
            QMessageBox.information(
                self, "No Duplicates Found 🎉",
                "This folder has no duplicate files.\nYour storage looks clean!"
            )
            return

        self._populate_dup_tree(groups)
        self._update_stats(groups)

        if self._sidebar.auto_cb.isChecked():
            self._select_dupes()

        self._sidebar.set_results_available(True)
        self._status.showMessage(f"Done — {len(groups)} duplicate group(s) found.")

    def _on_error(self, msg: str) -> None:
        self._sidebar.set_scan_running(False)
        QMessageBox.critical(self, "Something went wrong", msg)
        self._status.showMessage("An error occurred.")

    def _on_scan_error(self, msg: str) -> None:
        self._scan_worker = None
        self._sidebar.set_results_available(False)
        self._on_error(msg)

    def _on_similarity_threshold_changed(self, value: int) -> None:
        self._similar_tab.threshold_value_lbl.setText(f"{value}%")

    def _start_similarity_scan(self) -> None:
        if not self._selected_root:
            QMessageBox.warning(
                self,
                "No Folder Selected",
                "Please click 'Browse Folder' to choose a folder first.",
            )
            return
        if self._any_worker_running():
            QMessageBox.information(
                self,
                "Scan Already Running",
                "Please stop the current scan before starting another one.",
            )
            return
        if is_protected_path(self._selected_root):
            QMessageBox.critical(
                self,
                "This Folder is Protected",
                "You've selected a Windows system folder - scanning it could be harmful.\n\n"
                "Please choose a personal folder like Documents, Downloads, or Desktop.",
            )
            return

        self._similar_tab.sim_tree.clear()
        self._similar_tab.count_lbl.setText("")
        self._similar_tab.set_scan_running(True)
        self._similar_tab.set_results_available(False)

        self._similar_worker = SimilarityWorker(
            root=self._selected_root,
            threshold=self._similar_tab.threshold_slider.value(),
            workers=optimal_workers(),
        )
        self._similar_worker.progress.connect(self._on_progress)
        self._similar_worker.finished.connect(self._on_similarity_done)
        self._similar_worker.error.connect(self._on_similarity_error)
        self._similar_worker.start()

        self._tabs.setCurrentWidget(self._similar_tab)
        self._status.showMessage("Scanning similar files...")

    def _on_similarity_done(self, groups: list) -> None:
        self._similar_worker = None
        self._similar_tab.set_scan_running(False)

        if not groups:
            self._status.showMessage("No similar files found.")
            self._similar_tab.set_results_available(False)
            QMessageBox.information(
                self,
                "No Similar Files Found",
                "No perceptually similar media files were found in this folder.",
            )
            return

        self._populate_similarity_tree(groups)
        self._similar_tab.set_results_available(True)
        self._status.showMessage(f"Done - {len(groups)} similar group(s) found.")

    def _on_similarity_error(self, msg: str) -> None:
        self._similar_worker = None
        self._similar_tab.set_scan_running(False)
        self._similar_tab.set_results_available(False)
        QMessageBox.critical(self, "Similarity scan failed", msg)
        self._status.showMessage("An error occurred.")

    # ── Duplicate tree ────────────────────────────────────────────────────────

    def _populate_dup_tree(self, groups: list[DuplicateGroup]) -> None:
        tree = self._scan_tab.dup_tree
        tree.clear()
        tree.setSortingEnabled(False)
        total_files = 0

        for g in groups:
            bg_color   = QColor(GROUP_COLORS[g.group_id % len(GROUP_COLORS)])
            match_str  = {"hash": "HASH", "name": "NAME", "both": "BOTH"}.get(
                g.match_type, g.match_type.upper()
            )
            group_size = sum(f.size for f in g.files)

            gh = QTreeWidgetItem()
            gh.setText(0, f"  ▸ Group {g.group_id + 1}  ·  {len(g.files)} files  ·  {match_str}")
            gh.setText(3, fmt_size(group_size))
            for col in range(6):
                gh.setBackground(col, QBrush(bg_color))
            gh.setForeground(0, QBrush(QColor("#58a6ff")))
            font = QFont(); font.setBold(True); font.setPointSize(11)
            gh.setFont(0, font)
            gh.setFlags(gh.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            tree.addTopLevelItem(gh)

            for idx, fe in enumerate(g.files):
                ch = QTreeWidgetItem(gh)
                ch.setCheckState(0, Qt.CheckState.Unchecked)
                ch.setText(0, "    " + fe.name)
                ch.setText(1, f"G{g.group_id + 1}")
                ch.setText(2, match_str)
                ch.setText(3, fmt_size(fe.size))
                ch.setText(4, fe.path)
                ch.setText(5, (fe.hash_sha256[:22] + "…") if fe.hash_sha256 else "—")
                ch.setData(0, Qt.ItemDataRole.UserRole, fe)

                if idx == 0:
                    ch.setForeground(0, QBrush(QColor("#3fb950")))
                    ch.setToolTip(0, "✓ Original — kept by auto-select")
                if fe.protected:
                    ch.setForeground(0, QBrush(QColor("#f0883e")))
                    ch.setToolTip(0,
                        "⚠ Executable / script file — verify before deleting")
                total_files += 1

            gh.setExpanded(True)

        tree.setSortingEnabled(True)
        self._scan_tab.count_lbl.setText(f"{len(groups)} groups · {total_files} files")

    def _populate_similarity_tree(self, groups: list[DuplicateGroup]) -> None:
        tree = self._similar_tab.sim_tree
        tree.clear()
        tree.setSortingEnabled(False)
        total_files = 0

        for g in groups:
            bg_color = QColor(GROUP_COLORS[g.group_id % len(GROUP_COLORS)])
            kind_str = "IMAGE" if g.match_type == "image" else "AUDIO"
            group_size = sum(f.size for f in g.files)

            gh = QTreeWidgetItem()
            gh.setText(
                0,
                f"  ▸ Group {g.group_id + 1}  ·  {len(g.files)} files  ·  {kind_str}  ·  {g.similarity_score:.1f}%"
            )
            gh.setText(3, f"{g.similarity_score:.1f}%")
            gh.setText(4, fmt_size(group_size))
            for col in range(6):
                gh.setBackground(col, QBrush(bg_color))
            gh.setForeground(0, QBrush(QColor("#58a6ff")))
            font = QFont(); font.setBold(True); font.setPointSize(11)
            gh.setFont(0, font)
            gh.setFlags(gh.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            tree.addTopLevelItem(gh)

            for idx, fe in enumerate(g.files):
                ch = QTreeWidgetItem(gh)
                ch.setCheckState(0, Qt.CheckState.Unchecked)
                ch.setText(0, "    " + fe.name)
                ch.setText(1, f"G{g.group_id + 1}")
                ch.setText(2, kind_str)
                score = fe.similarity_score if fe.similarity_score > 0 else g.similarity_score
                ch.setText(3, f"{score:.1f}%")
                ch.setText(4, fmt_size(fe.size))
                ch.setText(5, fe.path)
                ch.setData(0, Qt.ItemDataRole.UserRole, fe)

                if idx == 0:
                    ch.setForeground(0, QBrush(QColor("#3fb950")))
                    ch.setToolTip(0, "Original - kept by auto-select")
                if fe.protected:
                    ch.setForeground(0, QBrush(QColor("#f0883e")))
                    ch.setToolTip(0, "System / protected file - verify before deleting")
                total_files += 1

            gh.setExpanded(True)

        tree.setSortingEnabled(True)
        self._sync_tree_count(tree, self._similar_tab.count_lbl)

    # ── Storage tree ──────────────────────────────────────────────────────────

    def _load_storage_tree(self) -> None:
        if not self._selected_root:
            return
        self._storage_tab.stor_tree.clear()
        self._storage_tab.chart.clear()
        self._sidebar.prog.setValue(0)
        self._sidebar.set_scan_running(True)

        self._storage_worker = StorageWorker(self._selected_root, _STORAGE_DEPTH)
        self._storage_worker.progress.connect(self._on_progress)
        self._storage_worker.finished.connect(self._on_storage_done)
        self._storage_worker.error.connect(self._on_error)
        self._storage_worker.start()

    def _on_storage_done(self, tree_data: dict) -> None:
        self._sidebar.set_scan_running(False)
        self._sidebar.prog.setValue(100)
        self._storage_loaded_for = self._selected_root

        stor = self._storage_tab.stor_tree
        stor.clear()

        # ── Populate the colour chart ── returns path→colour map
        colour_map = self._storage_tab.chart.set_data(tree_data)

        # ── Set the max-size so the delegate can draw proportional bars ───────
        self._storage_tab.size_delegate.set_max_size(tree_data["size"])

        # ── Build the tree ────────────────────────────────────────────────────
        root_item = self._make_storage_item(stor, tree_data, colour="#58a6ff",
                                             colour_map=colour_map)
        root_item.setForeground(0, QBrush(QColor("#58a6ff")))
        fnt = root_item.font(0); fnt.setBold(True); fnt.setPointSize(12)
        root_item.setFont(0, fnt)
        root_item.setExpanded(True)

        size_str = fmt_size(tree_data["size"]) if tree_data["size"] else "—"
        self._status.showMessage(
            f"Storage loaded: {self._selected_root}  |  {size_str} total"
        )

    def _make_storage_item(
        self,
        parent,
        node: dict,
        colour: str = "#484f58",
        colour_map: dict | None = None,
    ) -> QTreeWidgetItem:
        """Recursively build the storage detail tree."""
        if isinstance(parent, QTreeWidget):
            item = QTreeWidgetItem()
            parent.addTopLevelItem(item)
        else:
            item = QTreeWidgetItem(parent)

        is_dir  = node["is_dir"]
        prot    = node["protected"]
        name    = node["name"]
        size    = node["size"]
        path    = node["path"]

        # Top-level children have their own colour from the chart palette
        row_colour = (colour_map or {}).get(path, colour)

        if is_dir:
            item.setText(0, "📁  " + name)
            item.setText(1, fmt_size(size) if size else "")
            item.setForeground(0, QBrush(QColor(row_colour)))
            fnt = item.font(0); fnt.setBold(True); item.setFont(0, fnt)
        else:
            item.setText(0, "📄  " + name)
            item.setText(1, fmt_size(size))
            file_col = QColor("#f0883e") if prot else QColor("#8b949e")
            item.setForeground(0, QBrush(file_col))
            if prot:
                item.setToolTip(0, "⚠  System / protected — deletion blocked")

        item.setText(2, path)

        # Store raw size + colour for the size-bar delegate
        from features.storage.chart import StorageChart
        item.setData(1, StorageChart.SIZE_ROLE,   size)
        item.setData(1, StorageChart.COLOUR_ROLE, row_colour)

        item.setData(0, Qt.ItemDataRole.UserRole,
                     {"path": path, "is_dir": is_dir, "protected": prot})

        for child_node in node.get("children", []):
            self._make_storage_item(item, child_node,
                                    colour=row_colour, colour_map=None)

        if is_dir and node.get("children"):
            item.setExpanded(True)

        return item

    # ── Context menus ─────────────────────────────────────────────────────────

    def _ctx_scan(self, pos: QPoint) -> None:
        tree = self._scan_tab.dup_tree
        item = tree.itemAt(pos)
        if not item or not item.parent():
            return
        fe: FileEntry = item.data(0, Qt.ItemDataRole.UserRole)
        if not fe:
            return

        menu = QMenu(self)
        a_open    = menu.addAction("📂  Show in File Explorer")
        menu.addSeparator()
        a_check   = menu.addAction("☑  Mark for deletion")
        a_uncheck = menu.addAction("☐  Unmark")
        menu.addSeparator()
        a_trash   = menu.addAction("🗑  Delete this file now")

        if is_protected_path(fe.path):
            a_trash.setEnabled(False)
            a_trash.setText("🔒  Delete  (blocked — system file)")

        chosen = menu.exec(tree.viewport().mapToGlobal(pos))
        if   chosen == a_open:    open_in_explorer(fe.path)
        elif chosen == a_check:   item.setCheckState(0, Qt.CheckState.Checked)
        elif chosen == a_uncheck: item.setCheckState(0, Qt.CheckState.Unchecked)
        elif chosen == a_trash:
            self._trash_paths(
                [fe.path],
                on_success=lambda: self._remove_scan_item(item),
            )

    def _ctx_similar(self, pos: QPoint) -> None:
        tree = self._similar_tab.sim_tree
        item = tree.itemAt(pos)
        if not item or not item.parent():
            return
        fe: FileEntry = item.data(0, Qt.ItemDataRole.UserRole)
        if not fe:
            return

        menu = QMenu(self)
        a_open = menu.addAction("Show in File Explorer")
        menu.addSeparator()
        a_check = menu.addAction("Mark for deletion")
        a_uncheck = menu.addAction("Unmark")
        menu.addSeparator()
        a_trash = menu.addAction("Delete this file now")

        if is_protected_path(fe.path):
            a_trash.setEnabled(False)
            a_trash.setText("Delete (blocked - system file)")

        chosen = menu.exec(tree.viewport().mapToGlobal(pos))
        if chosen == a_open:
            open_in_explorer(fe.path)
        elif chosen == a_check:
            item.setCheckState(0, Qt.CheckState.Checked)
        elif chosen == a_uncheck:
            item.setCheckState(0, Qt.CheckState.Unchecked)
        elif chosen == a_trash:
            self._trash_paths(
                [fe.path],
                on_success=lambda: self._remove_similar_item(item),
            )

    def _ctx_storage(self, pos: QPoint) -> None:
        tree  = self._storage_tab.stor_tree
        items = tree.selectedItems()
        if not items:
            return

        menu    = QMenu(self)
        a_open  = menu.addAction("📂  Show in File Explorer")
        menu.addSeparator()
        a_trash = menu.addAction(f"🗑  Delete {len(items)} selected item(s)")
        chosen  = menu.exec(tree.viewport().mapToGlobal(pos))

        if chosen == a_open:
            data = items[0].data(0, Qt.ItemDataRole.UserRole)
            if data:
                open_in_explorer(data["path"])

        elif chosen == a_trash:
            sys_blocked = [
                it for it in items
                if is_protected_path(
                    (it.data(0, Qt.ItemDataRole.UserRole) or {}).get("path", "")
                )
            ]
            if sys_blocked:
                QMessageBox.warning(
                    self, "Some Items Are System Files",
                    f"{len(sys_blocked)} item(s) are in Windows system folders "
                    "and cannot be deleted.\n"
                    "Only your personal files will be removed.",
                )

            safe_items = [
                it for it in items
                if it.data(0, Qt.ItemDataRole.UserRole)
                and not is_protected_path(
                    it.data(0, Qt.ItemDataRole.UserRole).get("path", "")
                )
            ]
            paths = [it.data(0, Qt.ItemDataRole.UserRole)["path"] for it in safe_items]

            def _remove_from_tree():
                for it in safe_items:
                    parent = it.parent() or tree.invisibleRootItem()
                    parent.removeChild(it)

            self._trash_paths(paths, on_success=_remove_from_tree)

    # ── Deletion core ─────────────────────────────────────────────────────────

    def _trash_paths(
        self,
        paths:      list[str],
        on_success: Callable | None = None,
    ) -> None:
        """
        Move *paths* to the Recycle Bin with friendly, layered confirmation.

        Layer 1 — system paths are hard-blocked (PROTECTED_ROOTS).
        Layer 2 — files with executable extensions in USER paths: warn + ask.
        Layer 3 — main confirmation for everything else.
        """
        if not paths:
            return

        # ── Hard block: system-folder files ───────────────────────────────────
        sys_blocked = [p for p in paths if is_protected_path(p)]
        actionable  = [p for p in paths if not is_protected_path(p)]

        if not actionable:
            QMessageBox.warning(
                self, "Nothing to Delete",
                "The selected items are in Windows system folders and cannot be removed.\n"
                "Only files in your personal folders can be deleted."
            )
            return

        # ── Soft warn: executable / script extensions in user folders ─────────
        script_files = [p for p in actionable if is_protected_file(p)]
        safe         = actionable   # all non-system files are actionable

        if script_files:
            n = len(script_files)
            ext_list = ", ".join(
                sorted({Path(p).suffix.lower() for p in script_files})
            )
            warn_reply = QMessageBox.warning(
                self,
                "Executable Files Detected",
                f"{n} file(s) have program/script extensions ({ext_list}).\n\n"
                "These could be applications or scripts — not just data files.\n"
                "Are you sure you want to delete them too?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if warn_reply != QMessageBox.StandardButton.Yes:
                # Remove the script files from the deletion list
                safe = [p for p in actionable if not is_protected_file(p)]
                if not safe:
                    self._status.showMessage("Deletion cancelled.")
                    return

        # ── Main confirmation ─────────────────────────────────────────────────
        if len(safe) == 1:
            fname = Path(safe[0]).name
            msg   = f'Move "{fname}" to the Recycle Bin?\n\nYou can restore it later if needed.'
        else:
            msg   = (
                f"Move {len(safe)} file(s) to the Recycle Bin?\n\n"
                "You can restore them later if needed."
            )
        if sys_blocked:
            msg += f"\n\n⚠  {len(sys_blocked)} system file(s) were automatically skipped."

        reply = QMessageBox.question(
            self, "Confirm Deletion", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # ── Execute ───────────────────────────────────────────────────────────
        errors:  list[str] = []
        deleted: list[str] = []
        for p in safe:
            try:
                send2trash.send2trash(p)
                deleted.append(p)
            except Exception as exc:
                errors.append(f"{Path(p).name}: {exc}")

        if errors:
            QMessageBox.warning(
                self, "Some Files Couldn't Be Moved",
                "The following items could not be moved to the Recycle Bin:\n\n"
                + "\n".join(errors[:10])
                + ("\n…and more." if len(errors) > 10 else ""),
            )

        ok = len(deleted)
        if ok:
            suffix = f"  ({len(errors)} failed.)" if errors else ""
            self._status.showMessage(f"✓ {ok} file(s) moved to Recycle Bin.{suffix}")
            if on_success:
                on_success()

    def _delete_checked(self) -> None:
        """Delete all checked (marked) items in the duplicate scanner tree."""
        self._delete_checked_from_tree(
            self._scan_tab.dup_tree,
            self._scan_tab.count_lbl,
            "No files are currently marked for deletion.\n\n"
            "Tip: Check the boxes next to the files you want to remove, "
            "or click 'Select Dupes' to auto-mark all duplicates.",
            after_delete=lambda: QTimer.singleShot(800, self._start_scan),
        )

    def _delete_checked_similar(self) -> None:
        self._delete_checked_from_tree(
            self._similar_tab.sim_tree,
            self._similar_tab.count_lbl,
            "No files are currently marked for deletion.\n\n"
            "Tip: Check the boxes next to the files you want to remove, "
            "or click 'Select Close Matches' to auto-mark all but the first file in each group.",
        )

    # ── Tree helpers ──────────────────────────────────────────────────────────

    def _remove_scan_item(self, item: QTreeWidgetItem) -> None:
        tree   = self._scan_tab.dup_tree
        parent = item.parent()
        if not parent:
            return
        parent.removeChild(item)
        if parent.childCount() == 0:
            idx = tree.indexOfTopLevelItem(parent)
        if idx >= 0:
            tree.takeTopLevelItem(idx)
        self._sync_tree_count(tree, self._scan_tab.count_lbl)
        QTimer.singleShot(800, self._start_scan)

    def _remove_similar_item(self, item: QTreeWidgetItem) -> None:
        tree = self._similar_tab.sim_tree
        parent = item.parent()
        if not parent:
            return
        parent.removeChild(item)
        if parent.childCount() == 0:
            idx = tree.indexOfTopLevelItem(parent)
            if idx >= 0:
                tree.takeTopLevelItem(idx)
        self._sync_tree_count(tree, self._similar_tab.count_lbl)

    def _sync_count_label(self) -> None:
        self._sync_tree_count(self._scan_tab.dup_tree, self._scan_tab.count_lbl)

    # ── Select / clear ────────────────────────────────────────────────────────

    def _select_dupes(self) -> None:
        """
        Check all but the first (original) file in every group.
        Protected-extension files ARE included — safety is enforced at deletion.
        """
        tree = self._scan_tab.dup_tree
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                ch    = parent.child(j)
                state = Qt.CheckState.Unchecked if j == 0 else Qt.CheckState.Checked
                ch.setCheckState(0, state)

    def _clear_sel(self) -> None:
        tree = self._scan_tab.dup_tree
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                parent.child(j).setCheckState(0, Qt.CheckState.Unchecked)

    def _select_similar_dupes(self) -> None:
        self._select_all_but_first(self._similar_tab.sim_tree)

    def _clear_similar_sel(self) -> None:
        self._clear_tree_selection(self._similar_tab.sim_tree)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _update_stats(self, groups: list[DuplicateGroup]) -> None:
        dupes = sum(len(g.files) - 1 for g in groups)
        total = sum(len(g.files)     for g in groups)
        save  = sum(sum(f.size for f in g.files[1:]) for g in groups)
        prot  = sum(1 for g in groups for f in g.files if f.protected)

        sb = self._sidebar
        sb.s_groups.setText( f"Groups:              {len(groups)}")
        sb.s_dupes.setText(  f"Duplicates:          {dupes}")
        sb.s_save.setText(   f"Reclaimable:         {fmt_size(save)}")
        sb.s_scanned.setText(f"Files in groups:     {total}")
        sb.s_prot.setText(   f"Protected (locked):  {prot}")

        h = self._header
        h.c_groups.set_value(str(len(groups)))
        h.c_dupes.set_value(str(dupes))
        h.c_save.set_value(fmt_size(save))

    def _delete_checked_from_tree(
        self,
        tree: QTreeWidget,
        label,
        empty_message: str,
        after_delete: Callable | None = None,
    ) -> None:
        items_to_delete: list[tuple[str, QTreeWidgetItem]] = []

        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                ch = parent.child(j)
                if ch.checkState(0) == Qt.CheckState.Checked:
                    fe: FileEntry = ch.data(0, Qt.ItemDataRole.UserRole)
                    if fe:
                        items_to_delete.append((fe.path, ch))

        if not items_to_delete:
            QMessageBox.information(self, "Nothing Marked", empty_message)
            return

        paths = [p for p, _ in items_to_delete]
        tree_items = [item for _, item in items_to_delete]

        def _remove_from_tree() -> None:
            for item in tree_items:
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                    if parent.childCount() == 0:
                        idx = tree.indexOfTopLevelItem(parent)
                        if idx >= 0:
                            tree.takeTopLevelItem(idx)
            self._sync_tree_count(tree, label)
            if after_delete:
                after_delete()

        self._trash_paths(paths, on_success=_remove_from_tree)

    def _select_all_but_first(self, tree: QTreeWidget) -> None:
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                state = Qt.CheckState.Unchecked if j == 0 else Qt.CheckState.Checked
                child.setCheckState(0, state)

    def _clear_tree_selection(self, tree: QTreeWidget) -> None:
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                parent.child(j).setCheckState(0, Qt.CheckState.Unchecked)

    def _sync_tree_count(self, tree: QTreeWidget, label) -> None:
        groups = tree.topLevelItemCount()
        files = sum(tree.topLevelItem(i).childCount() for i in range(groups))
        g_s = "s" if groups != 1 else ""
        f_s = "s" if files != 1 else ""
        label.setText(f"{groups} group{g_s} · {files} file{f_s}")

    def _any_worker_running(self) -> bool:
        workers = [self._scan_worker, self._similar_worker, self._storage_worker]
        return any(worker is not None and worker.isRunning() for worker in workers)
