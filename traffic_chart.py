import math
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, QPoint, QRectF, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QFontMetrics
)
from PySide6.QtWidgets import QWidget, QSizePolicy
from network_monitor import NetworkMonitor


class TrafficChartWidget(QWidget):
    """
    Modern high-performance bar chart for network data usage visualization.
    Displays Download (Cyan Neon) and Upload (Emerald Neon) with interactive hover tooltips,
    adaptive Y-axis scaling, and Windows 11 Fluent dark glass aesthetic.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: List[Dict[str, Any]] = []
        self.hovered_index: Optional[int] = None
        self.mouse_pos: Optional[QPoint] = None

        self.down_color = "#00E5FF"
        self.up_color = "#00E676"

        self.setMouseTracking(True)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

    def set_colors(self, down_color: str, up_color: str):
        self.down_color = down_color or "#00E5FF"
        self.up_color = up_color or "#00E676"
        self.update()

    def set_data(self, data: List[Dict[str, Any]]):
        self.data = data
        self.hovered_index = None
        self.update()

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        new_hover = self._get_bar_index_at(event.pos().x())
        if new_hover != self.hovered_index:
            self.hovered_index = new_hover
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_index = None
        self.mouse_pos = None
        self.update()
        super().leaveEvent(event)

    def _get_bar_index_at(self, mouse_x: int) -> Optional[int]:
        if not self.data:
            return None

        w = self.width()
        padding_left = 60
        padding_right = 20
        plot_w = w - padding_left - padding_right
        if plot_w <= 0:
            return None

        n = len(self.data)
        col_w = plot_w / n
        if mouse_x < padding_left or mouse_x > (w - padding_right):
            return None

        idx = int((mouse_x - padding_left) / col_w)
        if 0 <= idx < n:
            return idx
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Background Card
        bg_rect = QRectF(0, 0, w, h)
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        painter.setBrush(QColor(20, 24, 32, 220))
        painter.drawRoundedRect(bg_rect, 10, 10)

        # Plot margins
        pad_l = 65
        pad_r = 20
        pad_t = 38
        pad_b = 32

        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b

        # 2. Draw Legend (Top Right)
        font_legend = QFont("Segoe UI", 8, QFont.Weight.DemiBold)
        painter.setFont(font_legend)

        # Download Legend
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.down_color))
        painter.drawRoundedRect(w - 190, 14, 10, 10, 3, 3)
        painter.setPen(QColor("#CBD5E1"))
        painter.drawText(w - 174, 23, "Download (▼)")

        # Upload Legend
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.up_color))
        painter.drawRoundedRect(w - 95, 14, 10, 10, 3, 3)
        painter.setPen(QColor("#CBD5E1"))
        painter.drawText(w - 79, 23, "Upload (▲)")

        if not self.data or plot_w <= 0 or plot_h <= 0:
            # Empty state
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, "Belum ada riwayat data untuk periode ini.")
            return

        # 3. Determine max value for Y-axis scale
        max_bytes = max((item["total_bytes"] for item in self.data), default=0)
        # At least 1 MB ceiling
        max_ceil = max(float(max_bytes), 1024.0 * 1024.0)

        # 4. Draw Horizontal Grid Lines & Y-Axis Labels
        painter.setFont(QFont("Segoe UI", 8))
        grid_steps = 4
        for i in range(grid_steps + 1):
            y = pad_t + plot_h - (i * (plot_h / grid_steps))
            val = (max_ceil / grid_steps) * i
            val_str = NetworkMonitor.format_bytes(val)

            # Grid line
            painter.setPen(QPen(QColor(255, 255, 255, 14 if i > 0 else 30), 1, Qt.PenStyle.SolidLine))
            painter.drawLine(int(pad_l), int(y), int(w - pad_r), int(y))

            # Y-axis Label
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(QRectF(4, y - 9, pad_l - 12, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, val_str)

        # 5. Draw Bars
        n = len(self.data)
        col_w = plot_w / float(n)
        bar_w = max(3.0, min(24.0, col_w * 0.65))

        # Determine label step for X-axis
        max_labels = max(4, int(plot_w / 50))
        label_step = max(1, math.ceil(n / max_labels))

        c_down = QColor(self.down_color)
        c_up = QColor(self.up_color)

        for i, item in enumerate(self.data):
            cx = pad_l + (i * col_w) + (col_w / 2.0)
            bx = cx - (bar_w / 2.0)

            recv_b = item["bytes_recv"]
            sent_b = item["bytes_sent"]

            # Height proportional
            recv_h = (recv_b / max_ceil) * plot_h
            sent_h = (sent_b / max_ceil) * plot_h

            is_hovered = (i == self.hovered_index)

            # Draw Download Bar (Bottom segment)
            base_y = pad_t + plot_h
            if recv_h > 0.5:
                ry = base_y - recv_h
                grad_down = QLinearGradient(bx, ry, bx, base_y)
                if is_hovered:
                    grad_down.setColorAt(0.0, c_down.lighter(130))
                    grad_down.setColorAt(1.0, c_down)
                else:
                    grad_down.setColorAt(0.0, c_down)
                    grad_down.setColorAt(1.0, c_down.darker(140))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad_down))
                # If no upload above it, round top corners
                radius = 3 if sent_h <= 0.5 else 0
                painter.drawRoundedRect(QRectF(bx, ry, bar_w, recv_h), radius, radius)

            # Draw Upload Bar (Stacked above Download)
            if sent_h > 0.5:
                sy = base_y - recv_h - sent_h
                grad_up = QLinearGradient(bx, sy, bx, base_y - recv_h)
                if is_hovered:
                    grad_up.setColorAt(0.0, c_up.lighter(130))
                    grad_up.setColorAt(1.0, c_up)
                else:
                    grad_up.setColorAt(0.0, c_up)
                    grad_up.setColorAt(1.0, c_up.darker(140))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(grad_up))
                painter.drawRoundedRect(QRectF(bx, sy, bar_w, sent_h), 3, 3)

            # Draw subtle pillar highlight if hovered
            if is_hovered:
                painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
                painter.setBrush(QColor(255, 255, 255, 12))
                painter.drawRoundedRect(QRectF(cx - (col_w / 2.0) + 1, pad_t, col_w - 2, plot_h), 4, 4)

            # Draw X-Axis Label
            if i % label_step == 0 or i == (n - 1):
                lbl = item.get("short_label", item.get("label", ""))
                painter.setPen(QColor("#38BDF8" if is_hovered else "#94A3B8"))
                painter.setFont(QFont("Segoe UI", 7 if n > 15 else 8))
                painter.drawText(QRectF(cx - 25, pad_t + plot_h + 6, 50, 18), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, lbl)

        # 6. Draw Tooltip for hovered column
        if self.hovered_index is not None and 0 <= self.hovered_index < len(self.data):
            item = self.data[self.hovered_index]
            self._draw_tooltip(painter, item, pad_l, pad_t, plot_w, plot_h)

    def _draw_tooltip(self, painter: QPainter, item: Dict[str, Any], pad_l: float, pad_t: float, plot_w: float, plot_h: float):
        time_label = item.get("label", "")
        down_str = NetworkMonitor.format_bytes(item["bytes_recv"])
        up_str = NetworkMonitor.format_bytes(item["bytes_sent"])
        total_str = NetworkMonitor.format_bytes(item["total_bytes"])

        title_text = f"Waktu: {time_label}"
        down_text = f"▼ Download: {down_str}"
        up_text = f"▲ Upload:   {up_str}"
        total_text = f"Total:       {total_str}"

        tip_w = 145.0
        tip_h = 76.0

        col_w = plot_w / float(len(self.data))
        cx = pad_l + (self.hovered_index * col_w) + (col_w / 2.0)

        tip_x = cx - (tip_w / 2.0)
        tip_y = pad_t + 10

        # Keep tooltip inside chart rectangle
        if tip_x < pad_l:
            tip_x = pad_l + 4
        elif tip_x + tip_w > (pad_l + plot_w):
            tip_x = pad_l + plot_w - tip_w - 4

        # Background box
        painter.setPen(QPen(QColor("#38BDF8"), 1))
        painter.setBrush(QColor(15, 23, 42, 245))
        painter.drawRoundedRect(QRectF(tip_x, tip_y, tip_w, tip_h), 7, 7)

        # Text lines
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#F8FAFC"))
        painter.drawText(int(tip_x + 8), int(tip_y + 16), title_text)

        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(self.down_color))
        painter.drawText(int(tip_x + 8), int(tip_y + 34), down_text)

        painter.setPen(QColor(self.up_color))
        painter.drawText(int(tip_x + 8), int(tip_y + 51), up_text)

        painter.setPen(QColor("#E2E8F0"))
        painter.drawText(int(tip_x + 8), int(tip_y + 68), total_text)
