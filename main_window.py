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
from features.scanner.worker import ScanWorker
from features.scanner.tab    import ScanTab
from features.storage.worker import StorageWorker
from features.storage.tab    import StorageTab
from features.ui.header      import AppHeader
from features.ui.sidebar     import Sidebar
from features.ui.style       import STYLE


class MainWindow(QMainWindow):
    """Top-level window — pure orchestration, no widget building."""

    APP_VERSION = "v3.1"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Redundant File Remover  {self.APP_VERSION}")
        self.setMinimumSize(1150, 720)
        self.resize(1400, 880)
        self._load_icon()

        # ── State ─────────────────────────────────────────────────────────────
        self._scan_worker:    Optional[ScanWorker]    = None
        self._storage_worker: Optional[StorageWorker] = None
        self._groups:         list[DuplicateGroup]    = []
        self._selected_root   = ""

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

        # Header
        self._header = AppHeader()
        root_lay.addWidget(self._header)

        # Body (sidebar + tabs)
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self._sidebar = Sidebar()
        body_lay.addWidget(self._sidebar)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._scan_tab    = ScanTab()
        self._storage_tab = StorageTab()
        self._tabs.addTab(self._scan_tab,    "⚡  Duplicate Scanner")
        self._tabs.addTab(self._storage_tab, "🗂  Storage Tree View")
        body_lay.addWidget(self._tabs, stretch=1)

        root_lay.addWidget(body, stretch=1)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — select a folder to begin.")

        self._wire_signals()

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        sb  = self._sidebar
        st  = self._scan_tab
        stt = self._storage_tab

        sb.browse_btn.clicked.connect(self._on_browse)
        sb.scan_btn.clicked.connect(self._start_scan)
        sb.stop_btn.clicked.connect(self._abort)
        sb.sel_btn.clicked.connect(self._select_dupes)
        sb.clr_btn.clicked.connect(self._clear_sel)
        sb.del_btn.clicked.connect(self._delete_checked)

        st.dup_tree.customContextMenuRequested.connect(self._ctx_scan)
        stt.load_btn.clicked.connect(self._load_storage_tree)
        stt.stor_tree.customContextMenuRequested.connect(self._ctx_storage)

    # ── Browse ────────────────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Folder", str(Path.home()))
        if not d:
            return
        self._selected_root = d

        # Truncate display path if too long
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
        if is_protected_path(self._selected_root):
            QMessageBox.critical(
                self, "This Folder is Protected",
                "You've selected a Windows system folder. Scanning it could be harmful.\n\n"
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
            workers=optimal_workers(),          # ← auto-detected, no user input needed
        )
        self._scan_worker.progress.connect(self._on_progress)
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.error.connect(self._on_error)
        self._scan_worker.start()

        self._tabs.setCurrentIndex(0)
        self._status.showMessage("Scanning…")

    def _abort(self) -> None:
        if self._scan_worker:
            self._scan_worker.abort()
        if self._storage_worker:
            self._storage_worker.abort()
        self._sidebar.set_scan_running(False)
        self._status.showMessage("Stopped.")

    # ── Progress slot ─────────────────────────────────────────────────────────

    def _on_progress(self, pct: int, msg: str) -> None:
        self._sidebar.prog.setValue(pct)
        self._status.showMessage(msg if len(msg) <= 90 else "…" + msg[-88:])

    # ── Scan done ─────────────────────────────────────────────────────────────

    def _on_scan_done(self, groups: list) -> None:
        self._groups = groups
        self._sidebar.set_scan_running(False)

        if not groups:
            self._status.showMessage("No duplicates found.")
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

    # ── Duplicate tree ────────────────────────────────────────────────────────

    def _populate_dup_tree(self, groups: list[DuplicateGroup]) -> None:
        tree = self._scan_tab.dup_tree
        tree.clear()
        tree.setSortingEnabled(False)
        total_files = 0

        for g in groups:
            bg_color   = QColor(GROUP_COLORS[g.group_id % len(GROUP_COLORS)])
            match_str  = "HASH" if g.match_type == "hash" else "NAME"
            group_size = sum(f.size for f in g.files)

            # Group header row
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

            # File child rows
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
                    ch.setToolTip(0, "🔒 Protected file — cannot be deleted")
                total_files += 1

            gh.setExpanded(True)

        tree.setSortingEnabled(True)
        self._scan_tab.count_lbl.setText(f"{len(groups)} groups · {total_files} files")

    # ── Storage tree ──────────────────────────────────────────────────────────

    def _load_storage_tree(self) -> None:
        if not self._selected_root:
            QMessageBox.warning(self, "No Folder Selected",
                "Please click 'Browse Folder' first.")
            return
        self._storage_tab.stor_tree.clear()
        self._sidebar.prog.setValue(0)
        self._sidebar.set_scan_running(True)

        self._storage_worker = StorageWorker(
            self._selected_root,
            self._storage_tab.depth_spin.value(),
        )
        self._storage_worker.progress.connect(self._on_progress)
        self._storage_worker.finished.connect(self._on_storage_done)
        self._storage_worker.error.connect(self._on_error)
        self._storage_worker.start()
        self._tabs.setCurrentIndex(1)

    def _on_storage_done(self, tree_data: dict) -> None:
        self._sidebar.set_scan_running(False)
        self._sidebar.prog.setValue(100)
        stor = self._storage_tab.stor_tree
        stor.clear()

        root_item = self._make_storage_item(stor, tree_data)
        root_item.setForeground(0, QBrush(QColor("#58a6ff")))
        f = root_item.font(0); f.setBold(True); f.setPointSize(12)
        root_item.setFont(0, f)
        root_item.setExpanded(True)

        size_str = fmt_size(tree_data["size"]) if tree_data["size"] else "—"
        self._status.showMessage(
            f"Tree loaded: {self._selected_root}  |  {size_str} total"
        )

    def _make_storage_item(self, parent, node: dict) -> QTreeWidgetItem:
        """Recursively build the storage tree."""
        if isinstance(parent, QTreeWidget):
            item = QTreeWidgetItem()
            parent.addTopLevelItem(item)
        else:
            item = QTreeWidgetItem(parent)

        is_dir = node["is_dir"]
        prot   = node["protected"]
        name   = node["name"]
        size   = node["size"]
        path   = node["path"]

        if is_dir:
            item.setText(0, "📁  " + name)
            item.setText(1, fmt_size(size) if size else "")
            item.setForeground(0, QBrush(QColor("#e3b341")))
            fnt = item.font(0); fnt.setBold(True); item.setFont(0, fnt)
        else:
            item.setText(0, "📄  " + name)
            item.setText(1, fmt_size(size))
            col = QColor("#f0883e") if prot else QColor("#8b949e")
            item.setForeground(0, QBrush(col))
            if prot:
                item.setToolTip(0, "🔒 System file — cannot be deleted")

        item.setText(2, path)
        item.setData(0, Qt.ItemDataRole.UserRole,
                     {"path": path, "is_dir": is_dir, "protected": prot})

        for child_node in node.get("children", []):
            self._make_storage_item(item, child_node)

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
        a_open   = menu.addAction("📂  Show in File Explorer")
        menu.addSeparator()
        a_check   = menu.addAction("☑  Mark for deletion")
        a_uncheck = menu.addAction("☐  Unmark")
        menu.addSeparator()
        a_trash   = menu.addAction("🗑  Delete this file now")

        if fe.protected:
            a_trash.setEnabled(False)
            a_trash.setText("🔒  Delete this file  (blocked — protected)")

        chosen = menu.exec(tree.viewport().mapToGlobal(pos))
        if   chosen == a_open:    open_in_explorer(fe.path)
        elif chosen == a_check:   item.setCheckState(0, Qt.CheckState.Checked)
        elif chosen == a_uncheck: item.setCheckState(0, Qt.CheckState.Unchecked)
        elif chosen == a_trash:
            # Remove from tree immediately, then trash
            self._trash_paths([fe.path], on_success=lambda: self._remove_scan_item(item))

    def _ctx_storage(self, pos: QPoint) -> None:
        tree  = self._storage_tab.stor_tree
        items = tree.selectedItems()
        if not items:
            return

        menu   = QMenu(self)
        a_open  = menu.addAction("📂  Show in File Explorer")
        menu.addSeparator()
        a_trash = menu.addAction(f"🗑  Delete {len(items)} selected item(s)")
        chosen  = menu.exec(tree.viewport().mapToGlobal(pos))

        if chosen == a_open:
            data = items[0].data(0, Qt.ItemDataRole.UserRole)
            if data:
                open_in_explorer(data["path"])

        elif chosen == a_trash:
            protected = [
                it for it in items
                if (it.data(0, Qt.ItemDataRole.UserRole) or {}).get("protected")
            ]
            if protected:
                QMessageBox.warning(
                    self, "Some Items Are Protected",
                    f"{len(protected)} item(s) are Windows system files and cannot be deleted.\n"
                    "Only your personal files will be removed.",
                )
            safe_items = [
                it for it in items
                if it.data(0, Qt.ItemDataRole.UserRole)
                and not it.data(0, Qt.ItemDataRole.UserRole).get("protected")
            ]
            paths = [it.data(0, Qt.ItemDataRole.UserRole)["path"] for it in safe_items]

            def _remove_storage_items():
                for it in safe_items:
                    parent = it.parent() or tree.invisibleRootItem()
                    parent.removeChild(it)

            self._trash_paths(paths, on_success=_remove_storage_items)

    # ── Deletion core ─────────────────────────────────────────────────────────

    def _trash_paths(
        self,
        paths:      list[str],
        on_success: Callable | None = None,
    ) -> None:
        """
        Move *paths* to the Recycle Bin with a friendly confirmation dialog.
        Calls *on_success()* after a successful (even partial) deletion.
        """
        if not paths:
            return

        # Double-check safety (never trust caller alone)
        safe    = [p for p in paths if not is_protected_path(p) and not is_protected_file(p)]
        blocked = len(paths) - len(safe)

        if not safe:
            QMessageBox.warning(
                self, "Nothing to Delete",
                "The selected items are Windows system files and cannot be deleted.\n"
                "Only files in your personal folders can be removed."
            )
            return

        # ── Compose a user-friendly confirmation message ───────────────────────
        if len(safe) == 1:
            fname = Path(safe[0]).name
            msg   = f"Move \"{fname}\" to the Recycle Bin?\n\nYou can restore it later if needed."
        else:
            msg   = f"Move {len(safe)} file(s) to the Recycle Bin?\n\nYou can restore them later if needed."

        if blocked:
            msg += (
                f"\n\n⚠  {blocked} protected system file(s) were automatically skipped."
            )

        reply = QMessageBox.question(
            self, "Confirm Deletion", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,   # default to No (safer)
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # ── Do the actual trash ───────────────────────────────────────────────
        errors: list[str] = []
        deleted: list[str] = []
        for p in safe:
            try:
                send2trash.send2trash(p)
                deleted.append(p)
            except Exception as exc:
                errors.append(f"{Path(p).name}: {exc}")

        if errors:
            QMessageBox.warning(
                self, "Some Files Couldn't Be Deleted",
                "The following files could not be moved to the Recycle Bin:\n\n"
                + "\n".join(errors[:10])
                + ("\n…and more." if len(errors) > 10 else ""),
            )

        ok = len(deleted)
        if ok:
            self._status.showMessage(
                f"✓ {ok} file(s) moved to Recycle Bin."
                + (f"  ({len(errors)} failed.)" if errors else "")
            )
            if on_success:
                on_success()

    def _delete_checked(self) -> None:
        """Delete all checked (marked) items in the duplicate scanner tree."""
        tree  = self._scan_tab.dup_tree
        items_to_delete: list[tuple[str, QTreeWidgetItem]] = []

        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                ch = parent.child(j)
                if ch.checkState(0) == Qt.CheckState.Checked:
                    fe: FileEntry = ch.data(0, Qt.ItemDataRole.UserRole)
                    if fe and not fe.protected:
                        items_to_delete.append((fe.path, ch))

        if not items_to_delete:
            QMessageBox.information(
                self, "Nothing Marked",
                "No files are currently marked for deletion.\n\n"
                "Tip: Check the boxes next to the files you want to remove, "
                "or click 'Select Dupes' to auto-mark all duplicates."
            )
            return

        paths      = [p    for p, _    in items_to_delete]
        tree_items = [item for _, item in items_to_delete]

        def _remove_from_tree():
            for item in tree_items:
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                    # Clean up empty group headers
                    if parent.childCount() == 0:
                        idx = tree.indexOfTopLevelItem(parent)
                        if idx >= 0:
                            tree.takeTopLevelItem(idx)
            self._sync_count_label()
            # Delayed re-scan to refresh stats
            QTimer.singleShot(800, self._start_scan)

        self._trash_paths(paths, on_success=_remove_from_tree)

    # ── Tree helpers ──────────────────────────────────────────────────────────

    def _remove_scan_item(self, item: QTreeWidgetItem) -> None:
        """Remove a single file item from the scanner tree; clean up empty groups."""
        tree   = self._scan_tab.dup_tree
        parent = item.parent()
        if not parent:
            return
        parent.removeChild(item)
        if parent.childCount() == 0:
            idx = tree.indexOfTopLevelItem(parent)
            if idx >= 0:
                tree.takeTopLevelItem(idx)
        self._sync_count_label()
        QTimer.singleShot(800, self._start_scan)

    def _sync_count_label(self) -> None:
        """Recount groups/files and update the count label after tree edits."""
        tree    = self._scan_tab.dup_tree
        groups  = tree.topLevelItemCount()
        files   = sum(
            tree.topLevelItem(i).childCount()
            for i in range(groups)
        )
        self._scan_tab.count_lbl.setText(
            f"{groups} group{'s' if groups != 1 else ''} · {files} file{'s' if files != 1 else ''}"
        )

    # ── Selection helpers ─────────────────────────────────────────────────────

    def _select_dupes(self) -> None:
        """Check all but the first (original) file in each group. Skip protected."""
        tree = self._scan_tab.dup_tree
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                ch = parent.child(j)
                fe: FileEntry = ch.data(0, Qt.ItemDataRole.UserRole)
                if fe and fe.protected:
                    ch.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    state = Qt.CheckState.Unchecked if j == 0 else Qt.CheckState.Checked
                    ch.setCheckState(0, state)

    def _clear_sel(self) -> None:
        tree = self._scan_tab.dup_tree
        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            for j in range(parent.childCount()):
                parent.child(j).setCheckState(0, Qt.CheckState.Unchecked)

    # ── Stats update ──────────────────────────────────────────────────────────

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
