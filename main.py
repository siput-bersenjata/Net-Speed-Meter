import sys
import os
import ctypes
import ctypes.wintypes
import traceback
from pathlib import Path

# Ensure project directory is on sys.path regardless of cwd
_project_dir = os.path.dirname(os.path.abspath(__file__))
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)
os.chdir(_project_dir)

# Ensure pythonw has valid stdout/stderr to prevent silent crashes
_log_dir = Path.home() / ".speed_meter"
_log_dir.mkdir(parents=True, exist_ok=True)

if sys.stdout is None:
    try:
        sys.stdout = open(_log_dir / "stdout.log", "a", encoding="utf-8")
    except Exception:
        sys.stdout = open(os.devnull, "w")

if sys.stderr is None:
    try:
        sys.stderr = open(_log_dir / "stderr.log", "a", encoding="utf-8")
    except Exception:
        sys.stderr = open(os.devnull, "w")

def global_excepthook(exc_type, exc_val, exc_tb):
    try:
        with open(_log_dir / "crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- Exception at {traceback.format_exc()} ---\n")
    except Exception:
        pass

sys.excepthook = global_excepthook

import win32event
import win32api
import winerror
import win32gui
import win32con

from PySide6.QtCore import Qt, QAbstractNativeEventFilter, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config_manager import ConfigManager
from network_monitor import NetworkMonitor
from widget_window import SpeedMeterWidget
from tray_manager import TrayManager
from settings_dialog import SettingsDialog

# Windows Message for single-instance inter-process activation
WM_SPEEDMETER_ACTIVATE = win32gui.RegisterWindowMessage("ModernSpeedMeter_Activate_Msg")


class WinActivationFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_SPEEDMETER_ACTIVATE:
                self.callback()
                return True, 0
        return False, 0


def log_step(msg):
    try:
        log_path = Path.home() / ".speed_meter" / "step.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def main():
    log_step(f"[main] Starting Speed Meter with args: {sys.argv}")
    # 1. Single-Instance Check using Windows Native Mutex
    mutex_name = "ModernSpeedMeter_SingleInstance_Mutex_v1"
    mutex = win32event.CreateMutex(None, False, mutex_name)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        log_step("[main] Already running. Writing show_settings trigger...")
        try:
            trigger_path = Path.home() / ".speed_meter" / "show_settings.trigger"
            trigger_path.parent.mkdir(parents=True, exist_ok=True)
            trigger_path.write_text("1", encoding="utf-8")
        except Exception:
            pass
        sys.exit(0)

    log_step("[main] Mutex acquired as primary instance.")

    # Windows AppUserModelID for crisp taskbar & notification branding
    try:
        myappid = "antigravity.speedmeter.modern.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    # High DPI Support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Ensure thread is attached to the interactive user desktop (WinSta0\Default)
    try:
        import win32service
        import win32con
        hDesk = win32service.OpenDesktop("Default", 0, False, win32con.GENERIC_ALL)
        if hDesk:
            ctypes.windll.user32.SetThreadDesktop(int(hDesk))
            log_step("[main] Switched thread desktop to WinSta0\\Default successfully.")
    except Exception as e:
        log_step(f"[main] SetThreadDesktop note: {e}")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # Set Application Icon
    icon_path = os.path.join(_project_dir, "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 1. Initialize Configuration
    config = ConfigManager()

    # 2. Initialize Floating Widget Window
    widget = SpeedMeterWidget(config_manager=config)

    # 3. Initialize Windows System Tray Manager
    tray = TrayManager(config_manager=config, parent=app)

    # 4. Initialize Network Monitoring Worker Thread
    interval_ms = config.get("refresh_interval_ms", 1000)
    nic_name = config.get("nic_name", "auto")
    monitor = NetworkMonitor(interval_ms=interval_ms, nic_name=nic_name, parent=app)

    # Wire telemetry signals
    def on_stats_updated(up_bps, down_bps, total_sent, total_recv, ping):
        try:
            widget.update_stats(up_bps, down_bps, total_sent, total_recv, ping)
            tray.update_tooltip(
                NetworkMonitor.format_speed(up_bps),
                NetworkMonitor.format_speed(down_bps),
                ping
            )
        except Exception:
            pass

    monitor.stats_updated.connect(on_stats_updated)

    # Wire Tray & Widget Actions
    def toggle_widget():
        if widget.isVisible():
            widget.hide()
            tray.update_toggle_text(False)
        else:
            widget.show()
            tray.update_toggle_text(True)

    tray.toggle_widget_requested.connect(toggle_widget)
    tray.dock_taskbar_requested.connect(widget.dock_to_taskbar)
    tray.snap_requested.connect(widget.snap_to_taskbar)
    tray.mode_change_requested.connect(widget.set_mode)
    tray.click_through_requested.connect(widget.set_click_through)
    tray.shape_template_requested.connect(widget.set_shape_template)

    widget.click_through_toggled.connect(tray.update_click_through_state)
    widget.shape_template_changed.connect(tray.update_shape_template_state)

    # Settings Dialog handler
    settings_dialog = None

    def open_settings():
        nonlocal settings_dialog
        if settings_dialog is None:
            settings_dialog = SettingsDialog(config_manager=config, parent=None)
            settings_dialog.dock_taskbar_requested.connect(widget.dock_to_taskbar)
            settings_dialog.snap_requested.connect(widget.snap_to_taskbar)

            def on_settings_applied():
                new_mode = config.get("widget_mode", "capsule")
                new_shape = config.get("shape_template", "pill")
                new_click_through = bool(config.get("click_through", False))

                if new_mode == "taskbar" or config.get("is_taskbar_docked", False):
                    widget.dock_to_taskbar(True)
                else:
                    widget.set_mode(new_mode)
                    widget.set_scale(float(config.get("widget_scale", 1.0)))
                    widget.set_shape_template(new_shape)

                widget.set_click_through(new_click_through)
                tray.update_click_through_state(new_click_through)
                tray.update_shape_template_state(new_shape)

                flags = widget.windowFlags()
                if config.get("always_on_top", True):
                    flags |= Qt.WindowType.WindowStaysOnTopHint
                else:
                    flags &= ~Qt.WindowType.WindowStaysOnTopHint
                widget.setWindowFlags(flags)
                widget.apply_click_through()
                widget.show()

                new_interval = config.get("refresh_interval_ms", 1000)
                new_nic = config.get("nic_name", "auto")
                monitor.set_interval(new_interval)
                monitor.set_nic(new_nic)

            settings_dialog.settings_changed.connect(on_settings_applied)

        settings_dialog.show()
        settings_dialog.raise_()
        settings_dialog.activateWindow()

    widget.settings_requested.connect(open_settings)
    tray.settings_requested.connect(open_settings)

    # IPC Trigger watcher for shortcut clicks
    trigger_path = Path.home() / ".speed_meter" / "show_settings.trigger"

    def check_trigger_file():
        if trigger_path.exists():
            log_step("[main] Trigger file detected! Bringing widget and settings to front.")
            try:
                trigger_path.unlink()
            except Exception:
                pass
            widget.show()
            widget.raise_()
            widget.activateWindow()
            open_settings()

    trigger_timer = QTimer(app)
    trigger_timer.timeout.connect(check_trigger_file)
    trigger_timer.start(350)

    # Clean Exit handler
    def exit_application():
        log_step("[exit_application] Clean exit requested.")
        monitor.stop()
        tray.tray_icon.hide()
        if settings_dialog:
            settings_dialog.close()
        app.quit()

    app.aboutToQuit.connect(lambda: log_step("[app] aboutToQuit signal fired!"))
    widget.exit_requested.connect(exit_application)
    tray.exit_requested.connect(exit_application)

    # Start Monitor & Show Widget
    log_step("[main] Starting monitor and showing widget...")
    monitor.start()
    widget.show()
    widget.raise_()

    # Automatically open Settings on first run or when requested so user clearly sees the app
    show_settings = "--settings" in sys.argv or getattr(config, "is_first_run", False)
    if show_settings:
        log_step("[main] Opening settings dialog...")
        open_settings()

    # Show system notification to let user know it's active
    tray.show_notification(
        "⚡ Speed Meter Aktif",
        "Widget kecepatan internet sedang berjalan. Klik kanan pada widget untuk pengaturan."
    )

    log_step("[main] Entering app.exec() event loop...")
    exit_code = app.exec()
    log_step(f"[main] app.exec() returned with code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_path = Path.home() / ".speed_meter" / "crash.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print(f"[CRASH] {e}")
        traceback.print_exc()
        sys.exit(1)
