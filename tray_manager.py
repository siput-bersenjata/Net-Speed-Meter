import os
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

import styles
from config_manager import ConfigManager


def create_tray_icon() -> QIcon:
    """Returns application tray icon."""
    _dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(_dir, "app_icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)

    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setBrush(QColor("#0F172A"))
    painter.setPen(QColor("#38BDF8"))
    painter.drawEllipse(3, 3, size - 6, size - 6)

    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QPolygon

    # Neon arrow UP (Emerald)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#00E676"))
    up_poly = QPolygon([
        QPoint(18, 38), QPoint(26, 20), QPoint(34, 38),
        QPoint(30, 38), QPoint(30, 48), QPoint(22, 48), QPoint(22, 38)
    ])
    painter.drawPolygon(up_poly)

    # Neon arrow DOWN (Cyan)
    painter.setBrush(QColor("#00E5FF"))
    down_poly = QPolygon([
        QPoint(34, 28), QPoint(42, 46), QPoint(50, 28),
        QPoint(46, 28), QPoint(46, 18), QPoint(38, 18), QPoint(38, 28)
    ])
    painter.drawPolygon(down_poly)

    painter.end()
    return QIcon(pixmap)


class TrayManager(QObject):
    """
    Manages the Windows System Tray Icon, notifications, and tray context menu.
    """
    toggle_widget_requested = Signal()
    dock_taskbar_requested = Signal(bool)
    snap_requested = Signal()
    mode_change_requested = Signal(str)
    click_through_requested = Signal(bool)
    shape_template_requested = Signal(str)
    settings_requested = Signal()
    exit_requested = Signal()

    def __init__(self, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.config = config_manager or ConfigManager()

        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self)
        self.tray_icon.setToolTip("Modern Speed Meter — Windows Network Monitor")

        self._setup_menu()
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _setup_menu(self):
        self.menu = QMenu()
        self.menu.setStyleSheet(styles.get_context_menu_style())

        header = self.menu.addAction("⚡ Speed Meter")
        header.setEnabled(False)

        self.menu.addSeparator()

        self.dock_act = self.menu.addAction("📌 Masuk ke Dalam Taskbar (Docked)")
        self.dock_act.triggered.connect(lambda: self.dock_taskbar_requested.emit(True))

        snap_act = self.menu.addAction("⚡ Snap ke Samping Wi-Fi")
        snap_act.triggered.connect(self.snap_requested.emit)

        self.toggle_act = self.menu.addAction("👁️ Sembunyikan Widget")
        self.toggle_act.triggered.connect(self.toggle_widget_requested.emit)

        mode_menu = self.menu.addMenu("🎨 Gaya Tampilan")
        mode_capsule = mode_menu.addAction("Capsule Pill (Kapsul Melayang)")
        mode_taskbar = mode_menu.addAction("Taskbar Docked (Di Dalam Taskbar)")
        mode_card = mode_menu.addAction("Floating Glass Card (Kartu Detail)")

        mode_capsule.triggered.connect(lambda: self.mode_change_requested.emit("capsule"))
        mode_taskbar.triggered.connect(lambda: self.dock_taskbar_requested.emit(True))
        mode_card.triggered.connect(lambda: self.mode_change_requested.emit("card"))

        # Shape Template Submenu
        self.tmpl_menu = self.menu.addMenu("📐 Template Bentuk")
        cur_tmpl = self.config.get("shape_template", "pill")
        self.tmpl_actions = {}
        for tmpl, label in [
            ("pill", "💊 Kapsul Bulat Penuh (Pill)"),
            ("badge", "🔘 Badge Melengkung (Badge)"),
            ("rounded", "🫧 Melengkung Modern (Rounded)"),
            ("text_only", "✨ Hanya Tulisan (Tanpa Background)")
        ]:
            act = self.tmpl_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(cur_tmpl == tmpl)
            act.triggered.connect(lambda checked=False, t=tmpl: self._on_template_selected(t))
            self.tmpl_actions[tmpl] = act

        self.menu.addSeparator()

        # Click-Through Toggle
        self.click_act = self.menu.addAction("🖱️ Mode Tembus Klik (Bisa Klik Tombol Belakang)")
        self.click_act.setCheckable(True)
        self.click_act.setChecked(self.config.get("click_through", False))
        self.click_act.triggered.connect(self._on_click_through_triggered)

        self.menu.addSeparator()

        settings_act = self.menu.addAction("⚙️ Pengaturan...")
        settings_act.triggered.connect(self.settings_requested.emit)

        exit_act = self.menu.addAction("❌ Keluar")
        exit_act.triggered.connect(self.exit_requested.emit)

        self.tray_icon.setContextMenu(self.menu)

    def _on_click_through_triggered(self):
        new_val = not self.config.get("click_through", False)
        self.config.set("click_through", new_val, auto_save=True)
        self.click_act.setChecked(new_val)
        self.click_through_requested.emit(new_val)
        if new_val:
            self.show_notification(
                "🖱️ Mode Tembus Klik Aktif",
                "Klik mouse sekarang langsung menembus ke tombol di belakangnya.\nBuka menu ikon tray untuk mematikan."
            )

    def _on_template_selected(self, tmpl: str):
        self.config.set("shape_template", tmpl, auto_save=True)
        for t, act in self.tmpl_actions.items():
            act.setChecked(t == tmpl)
        self.shape_template_requested.emit(tmpl)

    def update_click_through_state(self, enabled: bool):
        if hasattr(self, "click_act"):
            self.click_act.setChecked(enabled)

    def update_shape_template_state(self, tmpl: str):
        if hasattr(self, "tmpl_actions"):
            for t, act in self.tmpl_actions.items():
                act.setChecked(t == tmpl)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Single left-click
            self.toggle_widget_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def update_tooltip(self, up_str: str, down_str: str, ping: int = -1):
        ping_str = f" | {ping}ms" if ping >= 0 else ""
        self.tray_icon.setToolTip(f"Speed Meter\n▲ Up: {up_str}\n▼ Down: {down_str}{ping_str}")

    def update_toggle_text(self, is_visible: bool):
        if is_visible:
            self.toggle_act.setText("👁️ Sembunyikan Widget")
        else:
            self.toggle_act.setText("👁️ Tampilkan Widget")

    def show_notification(self, title: str, message: str, msec: int = 3000):
        try:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msec)
        except Exception:
            pass
