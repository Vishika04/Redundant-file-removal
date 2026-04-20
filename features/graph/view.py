"""
features/graph/view.py
Vertical Bar Chart visualization for Media Analytics.
Hardened for multi-bar visibility and stable layout.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore    import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui     import QPainter, QColor, QLinearGradient, QPen, QFont, QFontMetrics, QBrush
import math

# Updated Palette for consistency
KIND_COLORS = {
    "image":      "#2ea043", # Green
    "audio":      "#f2cc60", # Gold
    "video":      "#d299ff", # Purple
    "document":   "#f85149", # Red
    "archive":    "#a371f7", # Deep Purple
    "app":        "#ff7b72", # Coral
    "text":       "#316dca", # Blue
    "code":       "#58a6ff", # Light Blue
    "other":      "#8b949e"  # Grey
}

class BarChart(QWidget):
    """
    Vertical bar chart showing file counts by media kind.
    Hardened geometry to prevent clipping or invisible bars.
    """
    category_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[str, int] = {} 
        self._hovered: str = ""
        self._selected: str = ""
        
        self.setMinimumHeight(420)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_data(self, kind_counts: dict[str, int]):
        # Store all kinds that have > 0 counts
        new_data = {}
        for k, v in kind_counts.items():
            if v > 0:
                new_data[k] = v
        self._data = new_data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin_bottom = 100
        margin_left = 70
        margin_top = 70
        margin_right = 50
        
        draw_w = w - margin_left - margin_right
        draw_h = h - margin_top - margin_bottom
        
        # 1. Background
        p.fillRect(self.rect(), QColor("#161b22"))
        
        if not self._data:
            p.setPen(QColor("#484f58"))
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No media content found to visualize.")
            return

        # Use 100% as the target for the top of the grid if counts exist
        vals = list(self._data.values())
        max_val = max(vals) if vals else 1
        # Round up max_val for cleaner grid (e.g., if 33, maybe 40?)
        # For now, keep exact max_val to match labels.
        
        # 2. Grid & Axis
        p.setFont(QFont("Segoe UI", 9))
        ticks = 5
        for i in range(ticks + 1):
            val = int((max_val / ticks) * i)
            # Y coord from bottom
            y = h - margin_bottom - (i / ticks) * draw_h
            
            p.setPen(QColor("#8b949e"))
            p.drawText(margin_left - 60, int(y + 5), 50, 20, Qt.AlignmentFlag.AlignRight, str(val))
            
            p.setPen(QPen(QColor("#30363d"), 1, Qt.PenStyle.SolidLine if i==0 else Qt.PenStyle.DashLine))
            p.drawLine(margin_left, int(y), w - margin_right, int(y))

        # 3. Draw Bars
        # Sort kinds so they appear in a consistent order (largest first looks better)
        kinds = sorted(self._data.keys(), key=lambda k: self._data[k], reverse=True)
        
        bar_gap = 50
        num_bars = len(kinds)
        
        # Calculate bar width based on available space
        bar_w = (draw_w - (num_bars * bar_gap)) / num_bars
        bar_w = max(min(bar_w, 120), 40)
        
        # Center the bars group
        total_bar_block = (bar_w + bar_gap) * num_bars - bar_gap
        offset_x = (draw_w - total_bar_block) / 2
        
        for i, kind in enumerate(kinds):
            count = self._data[kind]
            pct = count / max_val
            
            # Bar geometry
            bh = int(pct * draw_h)
            if bh < 8: bh = 8 # Ensure tiny bars are visible
            
            bx = int(margin_left + offset_x + (i * (bar_w + bar_gap)))
            by = int(h - margin_bottom - bh)
            
            rect = QRectF(bx, by, bar_w, bh)
            is_active = (kind == self._hovered or kind == self._selected)
            color = QColor(KIND_COLORS.get(kind, "#8b949e"))

            if is_active:
                # Active Glow
                p.setPen(QPen(color.lighter(160), 4))
                p.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), 6, 6)

            # Bar Fill
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0, color.lighter(140))
            grad.setColorAt(0.5, color)
            grad.setColorAt(1, color.darker(130))
            
            p.setBrush(QBrush(grad))
            p.setPen(QPen(QColor("#ffffff"), 1.2))
            p.drawRoundedRect(rect, 6, 6)
            
            # Top Label (The Count)
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            p.drawText(bx, by - 25, int(bar_w), 20, Qt.AlignmentFlag.AlignCenter, str(count))
            
            # Bottom Label (The Kind)
            label_text = kind.upper()
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold if is_active else QFont.Weight.Normal))
            p.setPen(QColor("#ffffff" if is_active else "#f0f6fc"))
            
            label_metrics = QFontMetrics(p.font())
            tw = label_metrics.horizontalAdvance(label_text)
            
            label_rect_x = bx - (bar_gap // 4)
            label_rect_w = bar_w + (bar_gap // 2)
            
            if tw < label_rect_w:
                p.drawText(int(label_rect_x), h - margin_bottom + 10, int(label_rect_w), 30, Qt.AlignmentFlag.AlignCenter, label_text)
            else:
                p.save()
                p.translate(bx + bar_w/2, h - margin_bottom + 15)
                p.rotate(25)
                p.drawText(0, 0, label_text)
                p.restore()

    def mouseMoveEvent(self, event):
        pos = event.position()
        old = self._hovered
        self._hovered = ""
        
        kinds = sorted(self._data.keys(), key=lambda k: self._data[k], reverse=True)
        w, h = self.width(), self.height()
        margin_bottom, margin_left, margin_right = 100, 70, 50
        draw_w = w - margin_left - margin_right
        
        bar_gap = 50
        num_bars = len(kinds)
        if num_bars == 0: return
        
        bar_w = (draw_w - (num_bars * bar_gap)) / num_bars
        bar_w = max(min(bar_w, 120), 40)
        total_bar_block = (bar_w + bar_gap) * num_bars - bar_gap
        offset_x = (draw_w - total_bar_block) / 2

        for i, kind in enumerate(kinds):
            bx = margin_left + offset_x + (i * (bar_w + bar_gap))
            if bx <= pos.x() <= bx + bar_w:
                if 40 <= pos.y() <= h - margin_bottom:
                    self._hovered = kind
                    break
        
        if self._hovered != old: self.update()

    def mousePressEvent(self, event):
        if self._hovered:
            self._selected = self._hovered
            self.category_selected.emit(self._selected)
        else:
            self._selected = ""
            self.category_selected.emit("")
        self.update()
