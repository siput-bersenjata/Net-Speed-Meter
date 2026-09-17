import sys
import os
from collections import deque
from typing import Optional, List

from PySide6.QtCore import Qt, QPoint, Signal, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QAction, QCursor, QIcon, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QMenu, QFrame, QSizePolicy
)

import styles
from config_manager import ConfigManager
from network_monitor import NetworkMonitor
from win_utils import get_tray_wifi_dock_coordinate, clamp_to_screen, set_click_through_native


class SparklineWidget(QWidget):
    """Draws a sleek, modern real-time mini line graph of recent speeds."""
    def __init__(self, max_points: int = 25, height: int = 22, parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.history: deque = deque([0.0] * max_points, maxlen=max_points)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_value(self, val: float):
        self.history.append(val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        max_val = max(max(self.history), 1024.0)  # at least 1 KB/s ceiling

        points = []
        step_x = w / float(self.max_points - 1)
        for i, val in enumerate(self.history):
            x = i * step_x
            normalized = min(1.0, val / max_val)
            y = h - 2 - (normalized * (h - 4))
            points.append(QPoint(int(x), int(y)))

        if len(points) >= 2:
            # Gradient fill under line
            path_gradient = QLinearGradient(0, 0, 0, h)
            path_gradient.setColorAt(0.0, QColor(0, 229, 255, 60))
            path_gradient.setColorAt(1.0, QColor(0, 229, 255, 0))

            pen = QPen(QColor("#00E5FF"), 1.5)
            painter.setPen(pen)

            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])


class SpeedMeterWidget(QWidget):
    """
    Main floating network speed meter widget supporting:
    - 3 Modes: Capsule Pill, Taskbar Bar, and Glass Card.
    - Free dragging and position persistence.
    - Dynamic snap to Taskbar near Wi-Fi.
    - Frameless, translucent, and always on top.
    """
    settings_requested = Signal()
    exit_requested = Signal()
    click_through_toggled = Signal(bool)
    shape_template_changed = Signal(str)

    def __init__(self, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.config = config_manager or ConfigManager()

        self.drag_position = QPoint()
        self.is_dragging = False
        self.is_holding = False
        self.can_drag = False
        self.hold_timer = QTimer(self)
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self._on_hold_timeout)

        # Telemetry state
        self.current_up = 0.0
        self.current_down = 0.0
        self.current_total_sent = 0.0
        self.current_total_recv = 0.0
        self.current_ping = -1

        # Configure Window flags
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        if self.config.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Modern Speed Meter")

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self._restore_position()
        self.apply_theme()
        self.apply_click_through()

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_click_through()

    def apply_click_through(self, enable: Optional[bool] = None):
        """
        Enables or disables click-through on the widget window.
        When True, clicks, mouse moves, and scrolls pass directly to the window/taskbar behind it.
        """
        if enable is None:
            enable = bool(self.config.get("click_through", False))

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enable)
        try:
            hwnd = int(self.winId())
            set_click_through_native(hwnd, enable)
        except Exception as e:
            print(f"[SpeedMeterWidget] Note applying click through: {e}")

    def set_click_through(self, enable: bool):
        self.config.set("click_through", enable, auto_save=True)
        self.apply_click_through(enable)
        self.click_through_toggled.emit(enable)

    def set_shape_template(self, template: str):
        if template not in ["pill", "badge", "rounded", "text_only"]:
            template = "pill"
        self.config.set("shape_template", template, auto_save=True)
        self._setup_ui()
        self.apply_theme()
        if self.mode != "taskbar":
            self.adjustSize()
        self.update_stats(self.current_up, self.current_down, self.current_total_sent, self.current_total_recv, self.current_ping)
        self.apply_click_through()
        self.shape_template_changed.emit(template)

    def _setup_ui(self):
        # Clear layout if changing mode
        if self.layout():
            QWidget().setLayout(self.layout())

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.mode = self.config.get("widget_mode", "capsule")

        if self.mode == "taskbar":
            self._build_taskbar_ui()
        elif self.mode == "card":
            self._build_card_ui()
        else:
            self._build_capsule_ui()

    def _build_capsule_ui(self):
        scale = float(self.config.get("widget_scale", 1.0))
        shape_template = self.config.get("shape_template", "pill")
        self.central_container = QFrame(self)
        self.central_container.setObjectName("CentralCapsule")
        capsule_layout = QHBoxLayout(self.central_container)
        if shape_template == "text_only":
            pad_h = max(2, int(round(4 * scale)))
            pad_v = max(1, int(round(2 * scale)))
        else:
            pad_h = max(6, int(round(12 * scale)))
            pad_v = max(3, int(round(5 * scale)))
        capsule_layout.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        capsule_layout.setSpacing(max(3, int(round(6 * scale))))

        # Upload Indicator
        self.up_icon = QLabel("▲", self.central_container)
        self.up_icon.setObjectName("UpIcon")
        self.up_text = QLabel("0.0 B/s", self.central_container)
        self.up_text.setObjectName("SpeedText")

        # Divider
        self.divider = QLabel("•", self.central_container)
        self.divider.setStyleSheet(f"color: rgba(255, 255, 255, 0.25); font-size: {max(5, int(round(8 * scale)))}pt;")

        # Download Indicator
        self.down_icon = QLabel("▼", self.central_container)
        self.down_icon.setObjectName("DownIcon")
        self.down_text = QLabel("0.0 B/s", self.central_container)
        self.down_text.setObjectName("SpeedText")

        capsule_layout.addWidget(self.up_icon)
        capsule_layout.addWidget(self.up_text)
        capsule_layout.addWidget(self.divider)
        capsule_layout.addWidget(self.down_icon)
        capsule_layout.addWidget(self.down_text)

        self.main_layout.addWidget(self.central_container)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.adjustSize()

    def _build_taskbar_ui(self):
        scale = float(self.config.get("widget_scale", 1.0))
        shape_template = self.config.get("shape_template", "pill")
        self.central_container = QFrame(self)
        self.central_container.setObjectName("CentralTaskbar")
        bar_layout = QVBoxLayout(self.central_container)
        if shape_template == "text_only":
            pad_h = max(1, int(round(2 * scale)))
            pad_v = max(0, int(round(1 * scale)))
        else:
            pad_h = max(3, int(round(6 * scale)))
            pad_v = max(1, int(round(2 * scale)))
        bar_layout.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        bar_layout.setSpacing(0)

        # Row 1: Upload
        row_up = QHBoxLayout()
        row_up.setContentsMargins(0, 0, 0, 0)
        row_up.setSpacing(max(2, int(round(3 * scale))))
        self.up_icon = QLabel("▲", self.central_container)
        self.up_icon.setObjectName("UpIcon")
        self.up_text = QLabel("0.0 B/s", self.central_container)
        self.up_text.setObjectName("SpeedText")
        row_up.addWidget(self.up_icon)
        row_up.addWidget(self.up_text)
        row_up.addStretch()

        # Row 2: Download
        row_down = QHBoxLayout()
        row_down.setContentsMargins(0, 0, 0, 0)
        row_down.setSpacing(max(2, int(round(3 * scale))))
        self.down_icon = QLabel("▼", self.central_container)
        self.down_icon.setObjectName("DownIcon")
        self.down_text = QLabel("0.0 B/s", self.central_container)
        self.down_text.setObjectName("SpeedText")
        row_down.addWidget(self.down_icon)
        row_down.addWidget(self.down_text)
        row_down.addStretch()

        bar_layout.addLayout(row_up)
        bar_layout.addLayout(row_down)

        self.main_layout.addWidget(self.central_container)

        # Fixed sizing for seamless taskbar integration
        if shape_template == "text_only":
            tw = max(68, int(round(78 * scale)))
            th = max(24, int(round(30 * scale)))
        else:
            tw = max(76, int(round(90 * scale)))
            th = max(26, int(round(34 * scale)))
        self.setFixedSize(tw, th)

    def _build_card_ui(self):
        scale = float(self.config.get("widget_scale", 1.0))
        self.central_container = QFrame(self)
        self.central_container.setObjectName("CentralCard")
        card_layout = QVBoxLayout(self.central_container)
        pad_h = max(6, int(round(12 * scale)))
        pad_v = max(5, int(round(10 * scale)))
        card_layout.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        card_layout.setSpacing(max(3, int(round(6 * scale))))

        # Header: Title + Ping Badge
        header_layout = QHBoxLayout()
        header_title = QLabel("NET SPEED", self.central_container)
        header_title.setObjectName("HeaderTitle")
        self.ping_badge = QLabel("• ms", self.central_container)
        self.ping_badge.setObjectName("BadgePing")

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.ping_badge)
        card_layout.addLayout(header_layout)

        # Speeds row
        speeds_layout = QHBoxLayout()
        self.up_icon = QLabel("▲", self.central_container)
        self.up_icon.setObjectName("UpIcon")
        self.up_text = QLabel("0.0 B/s", self.central_container)
        self.up_text.setObjectName("CardSpeedUp")

        self.down_icon = QLabel("▼", self.central_container)
        self.down_icon.setObjectName("DownIcon")
        self.down_text = QLabel("0.0 B/s", self.central_container)
        self.down_text.setObjectName("CardSpeedDown")

        speeds_layout.addWidget(self.up_icon)
        speeds_layout.addWidget(self.up_text)
        speeds_layout.addSpacing(max(4, int(round(10 * scale))))
        speeds_layout.addWidget(self.down_icon)
        speeds_layout.addWidget(self.down_text)
        speeds_layout.addStretch()
        card_layout.addLayout(speeds_layout)

        # Mini Sparkline
        spark_h = max(14, int(round(22 * scale)))
        old_history = list(self.sparkline.history) if hasattr(self, "sparkline") and self.sparkline else None
        self.sparkline = SparklineWidget(height=spark_h, parent=self.central_container)
        if old_history:
            self.sparkline.history = deque(old_history, maxlen=self.sparkline.max_points)
        card_layout.addWidget(self.sparkline)

        # Footer: Total Session Usage
        s_up = NetworkMonitor.format_bytes(self.current_total_sent)
        s_down = NetworkMonitor.format_bytes(self.current_total_recv)
        self.session_label = QLabel(f"Session: ▲ {s_up}  ▼ {s_down}", self.central_container)
        self.session_label.setObjectName("SessionTotal")
        card_layout.addWidget(self.session_label)

        self.main_layout.addWidget(self.central_container)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.adjustSize()

    def apply_theme(self, is_drag_mode: bool = False):
        opacity = float(self.config.get("opacity", 0.92))
        up_col = self.config.get("up_color", "#00E676")
        down_col = self.config.get("down_color", "#00E5FF")
        font_family = self.config.get("font_family", "Segoe UI Variable Display, Segoe UI, sans-serif")
        font_size = int(self.config.get("font_size", 9))
        scale = float(self.config.get("widget_scale", 1.0))
        shape_template = self.config.get("shape_template", "pill")

        if self.mode == "taskbar":
            qss = styles.get_taskbar_style(opacity, up_col, down_col, font_family, font_size - 1, scale=scale, is_drag_mode=is_drag_mode, shape_template=shape_template)
        elif self.mode == "card":
            qss = styles.get_card_style(opacity, up_col, down_col, font_family, font_size, scale=scale, is_drag_mode=is_drag_mode, shape_template=shape_template)
        else:
            qss = styles.get_capsule_style(opacity, up_col, down_col, font_family, font_size, scale=scale, is_drag_mode=is_drag_mode, shape_template=shape_template)

        self.setStyleSheet(qss)

    def update_stats(self, up_rate: float, down_rate: float, total_sent: float, total_recv: float, ping: int):
        self.current_up = up_rate
        self.current_down = down_rate
        self.current_total_sent = total_sent
        self.current_total_recv = total_recv
        self.current_ping = ping

        up_str = NetworkMonitor.format_speed(up_rate)
        down_str = NetworkMonitor.format_speed(down_rate)

        self.up_text.setText(up_str)
        self.down_text.setText(down_str)

        if self.mode == "card":
            if hasattr(self, "sparkline"):
                self.sparkline.add_value(down_rate + up_rate)
            if hasattr(self, "ping_badge"):
                if ping >= 0:
                    self.ping_badge.setText(f"{ping} ms")
                    if ping < 60:
                        self.ping_badge.setStyleSheet("color: #4ADE80; background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3);")
                    elif ping < 150:
                        self.ping_badge.setStyleSheet("color: #FBBF24; background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.3);")
                    else:
                        self.ping_badge.setStyleSheet("color: #F87171; background: rgba(248, 113, 113, 0.15); border: 1px solid rgba(248, 113, 113, 0.3);")
                else:
                    self.ping_badge.setText("-- ms")
            if hasattr(self, "session_label"):
                s_up = NetworkMonitor.format_bytes(total_sent)
                s_down = NetworkMonitor.format_bytes(total_recv)
                self.session_label.setText(f"Session: ▲ {s_up}  ▼ {s_down}")

    def set_mode(self, mode: str):
        if mode not in ["capsule", "taskbar", "card"]:
            mode = "capsule"
        mode_changed = (self.mode != mode)
        self.mode = mode
        self.config.set("widget_mode", mode, auto_save=False)
        if mode == "taskbar":
            self.config.set("is_taskbar_docked", True, auto_save=False)
        else:
            self.config.set("is_taskbar_docked", False, auto_save=False)

        if mode_changed:
            self._setup_ui()
        self.apply_theme()
        self.update_stats(self.current_up, self.current_down, self.current_total_sent, self.current_total_recv, self.current_ping)

        if mode == "taskbar":
            self.dock_to_taskbar(True)
        else:
            self.adjustSize()
            screen = self.screen() or QGuiApplication.primaryScreen()
            avail = screen.availableGeometry() if screen else None
            if avail and (self.y() + self.height() > avail.bottom()):
                self.move(self.x(), max(avail.top() + 10, avail.bottom() - self.height() - 20))

    def dock_to_taskbar(self, enable: bool = True):
        """
        Docks or undocks the widget directly inside the Windows Taskbar
        adjacent to the system tray notification icons (^ chevron, Wi-Fi, battery).
        """
        if enable:
            self.mode = "taskbar"
            self.config.set("widget_mode", "taskbar", auto_save=False)
            self.config.set("is_taskbar_docked", True, auto_save=False)
            self._setup_ui()
            self.apply_theme()
            self.update_stats(self.current_up, self.current_down, self.current_total_sent, self.current_total_recv, self.current_ping)

            w = self.width() if self.width() > 0 else 82
            h = self.height() if self.height() > 0 else 34
            screen = self.screen() or QGuiApplication.primaryScreen()
            target_x, target_y = get_tray_wifi_dock_coordinate(w, h, screen=screen)

            self.move(int(target_x), int(target_y))
            self.config.set("pos_x", int(target_x), auto_save=False)
            self.config.set("pos_y", int(target_y), auto_save=True)
        else:
            self.config.set("is_taskbar_docked", False, auto_save=False)
            self.mode = "capsule"
            self.config.set("widget_mode", "capsule", auto_save=False)
            self._setup_ui()
            self.apply_theme()
            self.update_stats(self.current_up, self.current_down, self.current_total_sent, self.current_total_recv, self.current_ping)

            screen = self.screen() or QGuiApplication.primaryScreen()
            avail = screen.availableGeometry() if screen else None
            if avail:
                target_x = max(10, self.x())
                target_y = max(10, avail.height() - self.height() - 20)
            else:
                target_x, target_y = 100, 100

            self.move(int(target_x), int(target_y))
            self.config.set("pos_x", int(target_x), auto_save=False)
            self.config.set("pos_y", int(target_y), auto_save=True)

    def snap_to_taskbar(self):
        """Snaps widget directly to the left of the Windows Taskbar Wi-Fi / System Tray."""
        w = self.width() if self.width() > 0 else 82
        h = self.height() if self.height() > 0 else 34
        screen = self.screen() or QGuiApplication.primaryScreen()
        target_x, target_y = get_tray_wifi_dock_coordinate(w, h, screen=screen)
        self.move(int(target_x), int(target_y))
        self.config.set("pos_x", int(target_x), auto_save=False)
        self.config.set("pos_y", int(target_y), auto_save=True)

    def toggle_lock(self):
        locked = not self.config.get("locked_position", False)
        self.config.set("locked_position", locked)

    def toggle_always_on_top(self):
        ontop = not self.config.get("always_on_top", True)
        self.config.set("always_on_top", ontop)
        flags = self.windowFlags()
        if ontop:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _restore_position(self):
        if self.config.get("is_taskbar_docked", False):
            self.dock_to_taskbar(True)
            return

        w = max(60, self.width())
        h = max(20, self.height())

        screen = self.screen() or QGuiApplication.primaryScreen()
        screen_w = screen.geometry().width() if screen else 1536
        screen_h = screen.geometry().height() if screen else 864

        x = self.config.get("pos_x", None)
        y = self.config.get("pos_y", None)

        # If unset, default (100, 100), or off-screen, snap to taskbar
        if x is None or y is None or (x == 100 and y == 100) or y >= (screen_h - 10) or x >= (screen_w - 10):
            self.snap_to_taskbar()
        else:
            cx = max(4, min(int(x), screen_w - w - 4))
            cy = max(2, min(int(y), screen_h - h - 2))
            self.move(cx, cy)

    def _on_hold_timeout(self):
        if self.is_holding and not self.config.get("locked_position", False):
            self.can_drag = True
            self.is_dragging = True
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            self.apply_theme(is_drag_mode=True)

    # Mouse Events for Drag & Drop
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.config.get("locked_position", False):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                if self.config.get("hold_to_drag", True):
                    self.is_holding = True
                    self.can_drag = False
                    self.is_dragging = False
                    duration = int(self.config.get("hold_duration_ms", 2000))
                    self.hold_timer.start(duration)
                else:
                    self.can_drag = True
                    self.is_dragging = True
                event.accept()

    def mouseMoveEvent(self, event):
        if self.can_drag and self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hold_timer.stop()
            self.is_holding = False
            if self.can_drag and self.is_dragging:
                self.config.set("pos_x", self.x(), auto_save=False)
                self.config.set("pos_y", self.y(), auto_save=True)
                screen = self.screen() or QGuiApplication.primaryScreen()
                if screen:
                    avail = screen.availableGeometry()
                    # If dragged up into the desktop work area, unmark docked status
                    if self.y() + self.height() <= avail.height():
                        self.config.set("is_taskbar_docked", False, auto_save=True)
                    else:
                        self.config.set("is_taskbar_docked", True, auto_save=True)
            self.can_drag = False
            self.is_dragging = False
            self.unsetCursor()
            self.apply_theme(is_drag_mode=False)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hold_timer.stop()
            self.is_holding = False
            self.can_drag = False
            self.is_dragging = False
            self.settings_requested.emit()
            event.accept()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            current_scale = float(self.config.get("widget_scale", 1.0))
            if delta > 0:
                new_scale = min(1.50, current_scale + 0.05)
            else:
                new_scale = max(0.65, current_scale - 0.05)
            self.set_scale(new_scale)
            event.accept()
        else:
            super().wheelEvent(event)

    def set_scale(self, scale: float):
        scale = max(0.65, min(1.50, round(scale, 2)))
        self.config.set("widget_scale", scale, auto_save=True)
        self._setup_ui()
        self.apply_theme()
        if self.mode != "taskbar":
            self.adjustSize()
        self._clamp_current_position()

    def _clamp_current_position(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            screen_w = geom.width()
            screen_h = geom.height()
        else:
            screen_w, screen_h = 1536, 864
        w = max(self.width(), 60)
        h = max(self.height(), 20)
        cx = max(4, min(self.x(), screen_w - w - 4))
        cy = max(2, min(self.y(), screen_h - h - 2))
        self.move(cx, cy)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(styles.get_context_menu_style())

        is_docked = self.config.get("is_taskbar_docked", False)
        if is_docked:
            dock_act = menu.addAction("📌 Lepaskan dari Taskbar (Mode Melayang)")
            dock_act.triggered.connect(lambda: self.dock_to_taskbar(False))
        else:
            dock_act = menu.addAction("📌 Masuk ke Dalam Taskbar (Docked)")
            dock_act.triggered.connect(lambda: self.dock_to_taskbar(True))

        snap_action = menu.addAction("⚡ Snap ke Samping Wi-Fi")
        snap_action.triggered.connect(self.snap_to_taskbar)

        menu.addSeparator()

        # Mode Submenu
        mode_menu = menu.addMenu("🎨 Gaya Tampilan")
        act_capsule = mode_menu.addAction("Capsule Pill (Kapsul Melayang)")
        act_taskbar = mode_menu.addAction("Taskbar Docked (Di Dalam Taskbar)")
        act_card = mode_menu.addAction("Floating Glass Card (Kartu Detail)")

        act_capsule.triggered.connect(lambda: self.set_mode("capsule"))
        act_taskbar.triggered.connect(lambda: self.dock_to_taskbar(True))
        act_card.triggered.connect(lambda: self.set_mode("card"))

        # Shape Template Submenu
        tmpl_menu = menu.addMenu("📐 Template Bentuk")
        cur_tmpl = self.config.get("shape_template", "pill")
        act_pill = tmpl_menu.addAction("💊 Kapsul Bulat Penuh (Pill)")
        act_badge = tmpl_menu.addAction("🔘 Badge Melengkung (Badge)")
        act_rounded = tmpl_menu.addAction("🫧 Melengkung Modern (Rounded)")
        act_text = tmpl_menu.addAction("✨ Hanya Tulisan (Tanpa Background)")

        for act, tmpl in [
            (act_pill, "pill"),
            (act_badge, "badge"),
            (act_rounded, "rounded"),
            (act_text, "text_only")
        ]:
            act.setCheckable(True)
            act.setChecked(cur_tmpl == tmpl)
            act.triggered.connect(lambda checked=False, t=tmpl: self.set_shape_template(t))

        menu.addSeparator()

        click_act = menu.addAction("🖱️ Mode Tembus Klik (Bisa Klik Tombol Belakang)")
        click_act.setCheckable(True)
        click_act.setChecked(self.config.get("click_through", False))
        click_act.triggered.connect(lambda: self.set_click_through(not self.config.get("click_through", False)))

        lock_action = menu.addAction("🔒 Kunci Posisi")
        lock_action.setCheckable(True)
        lock_action.setChecked(self.config.get("locked_position", False))
        lock_action.triggered.connect(self.toggle_lock)

        top_action = menu.addAction("📌 Always on Top")
        top_action.setCheckable(True)
        top_action.setChecked(self.config.get("always_on_top", True))
        top_action.triggered.connect(self.toggle_always_on_top)

        menu.addSeparator()

        settings_action = menu.addAction("⚙️ Pengaturan...")
        settings_action.triggered.connect(self.settings_requested.emit)

        exit_action = menu.addAction("❌ Keluar")
        exit_action.triggered.connect(self.exit_requested.emit)

        menu.exec(QCursor.pos())
