"""
features/storage/chart.py

StorageChart  — proportional horizontal-bar chart showing disk usage.
SizeBarDelegate — custom painter for the "Size" column in the detail tree.
"""

from PyQt6.QtWidgets import QWidget, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtCore    import Qt, QRectF, QSize, pyqtSignal
from PyQt6.QtGui     import (
    QPainter, QColor, QLinearGradient, QPen, QFont,
    QFontMetrics, QBrush,
)

from features.core.utils import fmt_size


# 12 accessible, distinct accent colours for chart segments
CHART_PALETTE: tuple[str, ...] = (
    "#1f6feb", "#3fb950", "#e3b341", "#f85149",
    "#bc8cff", "#79c0ff", "#ff7b72", "#56d364",
    "#d29922", "#388bfd", "#a8dadc", "#4d8a69",
)


# ─────────────────────────── Chart widget ───────────────────────────────────

class StorageChart(QWidget):
    """
    Horizontal proportional bar chart.

    Call  set_data(tree_dict)  to populate.
    Returns a  {path: colour_hex}  mapping to colour-match tree rows.
    Emits  segment_clicked(path)  when the user clicks a segment.
    """

    segment_clicked = pyqtSignal(str)

    _BAR_H   = 84          # fixed widget height
    _RADIUS  = 5.0         # rounded corners
    _MARGIN  = 4           # left/right outer margin

    # Per-item data roles used by SizeBarDelegate
    SIZE_ROLE   = Qt.ItemDataRole.UserRole + 1
    COLOUR_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments: list[dict] = []
        self._total:    int        = 0
        self._hovered:  int        = -1
        self._empty:    bool       = True

        self.setFixedHeight(self._BAR_H)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── public API ────────────────────────────────────────────────────────────

    def set_data(self, tree_data: dict) -> dict[str, str]:
        """
        Populate chart from a StorageWorker tree dict.
        Returns  {child_path: hex_colour}  for tree row tinting.
        """
        children = sorted(
            tree_data.get("children", []),
            key=lambda c: c["size"],
            reverse=True,
        )
        self._total    = tree_data.get("size", 0)
        self._segments = []
        colour_map: dict[str, str] = {}

        for i, child in enumerate(children):
            colour = CHART_PALETTE[i % len(CHART_PALETTE)]
            self._segments.append({
                "name":   child["name"],
                "size":   child["size"],
                "path":   child["path"],
                "is_dir": child["is_dir"],
                "colour": colour,
                "rect":   None,      # computed during paintEvent
            })
            colour_map[child["path"]] = colour

        self._empty   = False
        self._hovered = -1
        self.update()
        return colour_map

    def clear(self) -> None:
        self._segments = []
        self._total    = 0
        self._empty    = True
        self._hovered  = -1
        self.update()

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        p.fillRect(0, 0, w, h, QColor("#010409"))

        # ── Placeholder ───────────────────────────────────────────────────────
        if self._empty or not self._segments or not self._total:
            p.setPen(QColor("#30363d"))
            p.setFont(_font(11))
            p.drawText(
                0, 0, w, h, Qt.AlignmentFlag.AlignCenter,
                "Storage chart will appear here after a folder is selected",
            )
            p.end()
            return

        # Subtle outer border
        p.setPen(QPen(QColor("#21262d"), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), self._RADIUS, self._RADIUS)
        p.setPen(Qt.PenStyle.NoPen)

        m     = self._MARGIN
        bar_h = h - 2 * m
        avail = w - 2 * m
        x     = float(m)

        for i, seg in enumerate(self._segments):
            if not seg["size"]:
                continue

            seg_w  = max(avail * seg["size"] / self._total, 2.0)
            rect   = QRectF(x, m, seg_w - 1, bar_h)
            seg["rect"] = rect

            base  = QColor(seg["colour"])
            hov   = i == self._hovered

            top_c = base.lighter(150 if hov else 125)
            bot_c = base.darker( 140 if hov else 115)

            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0.0, top_c)
            grad.setColorAt(0.5, base)
            grad.setColorAt(1.0, bot_c)

            p.setBrush(QBrush(grad))
            border_col = base.lighter(200) if hov else QColor("#00000050")
            p.setPen(QPen(border_col, 0.8))
            p.drawRoundedRect(rect, self._RADIUS, self._RADIUS)
            p.setPen(Qt.PenStyle.NoPen)

            # Text
            if seg_w > 28:
                text_r = rect.adjusted(4, 4, -4, -4)
                p.setPen(QColor("#ffffffff" if hov else "#e0e0e0"))

                if seg_w > 70:
                    # Two lines: name + size
                    half = text_r.height() / 2
                    nm_r = QRectF(text_r.x(), text_r.y(),          text_r.width(), half)
                    sz_r = QRectF(text_r.x(), text_r.y() + half,   text_r.width(), half)

                    name_font = _font(10, bold=True)
                    p.setFont(name_font)
                    name_elided = QFontMetrics(name_font).elidedText(
                        seg["name"], Qt.TextElideMode.ElideRight, int(text_r.width())
                    )
                    p.drawText(nm_r, Qt.AlignmentFlag.AlignCenter, name_elided)

                    p.setFont(_font(9))
                    p.drawText(sz_r, Qt.AlignmentFlag.AlignCenter, fmt_size(seg["size"]))
                else:
                    p.setFont(_font(9))
                    p.drawText(text_r, Qt.AlignmentFlag.AlignCenter, fmt_size(seg["size"]))

            x += seg_w

        p.end()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        old = self._hovered
        self._hovered = -1
        for i, seg in enumerate(self._segments):
            r = seg.get("rect")
            if r and r.contains(pos):
                self._hovered = i
                icon = "📁" if seg["is_dir"] else "📄"
                self.setToolTip(
                    f"{icon}  {seg['name']}\n"
                    f"Size: {fmt_size(seg['size'])}\n"
                    f"Path: {seg['path']}"
                )
                break
        if self._hovered != old:
            self.update()

    def mousePressEvent(self, event) -> None:
        if self._hovered >= 0:
            self.segment_clicked.emit(self._segments[self._hovered]["path"])

    def leaveEvent(self, _event) -> None:
        if self._hovered != -1:
            self._hovered = -1
            self.update()


# ───────────────────────── Size-bar delegate ────────────────────────────────

class SizeBarDelegate(QStyledItemDelegate):
    """
    Renders a proportional colour bar in the Size column of QTreeWidget.
    Call  set_max_size(bytes)  once after loading the tree.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._max: int = 1

    def set_max_size(self, size: int) -> None:
        self._max = max(size, 1)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        if index.column() != 1:
            super().paint(painter, option, index)
            return

        raw    = index.data(StorageChart.SIZE_ROLE)
        colour = index.data(StorageChart.COLOUR_ROLE)

        if raw is None or not colour:
            super().paint(painter, option, index)
            return

        r = option.rect
        painter.save()

        # Row background
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        painter.fillRect(r, QColor("#1f6feb40" if sel else "#010409"))

        if raw > 0:
            pct   = min(raw / self._max, 1.0)
            bar_w = max(int(r.width() * pct), 2)
            bar_r = r.adjusted(0, 4, 0, -4)
            bar_r.setWidth(bar_w)

            c = QColor(colour)
            g = QLinearGradient(bar_r.topLeft(), bar_r.bottomLeft())
            g.setColorAt(0, c.lighter(130))
            g.setColorAt(1, c.darker(115))
            painter.fillRect(bar_r, QBrush(g))

        # Size label on top
        painter.setPen(QColor("#c9d1d9"))
        painter.setFont(_font(10))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, index.data() or "")

        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        h = super().sizeHint(option, index)
        return QSize(h.width(), 28)


# ── private util ─────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False) -> QFont:
    f = QFont("Segoe UI", size)
    if bold:
        f.setBold(True)
    return f
