"""Quick diagnostic launcher — prints progress to stdout so we can see where it stalls."""
import sys, os
sys.stdout.reconfigure(line_buffering=True)

print("[1/8] Importing modules...", flush=True)
import ctypes
from PySide6.QtCore import Qt, QSharedMemory
from PySide6.QtWidgets import QApplication
print("[1/8] OK", flush=True)

print("[2/8] Creating QApplication...", flush=True)
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
print("[2/8] OK", flush=True)

print("[3/8] Single-instance check...", flush=True)
sm = QSharedMemory("ModernSpeedMeter_SingleInstance_Key")
if not sm.create(1):
    sm.attach()
    sm.detach()
    if not sm.create(1):
        print("[3/8] BLOCKED — another instance is running! Exiting.", flush=True)
        sys.exit(1)
print("[3/8] OK — we are the only instance", flush=True)

print("[4/8] ConfigManager...", flush=True)
from config_manager import ConfigManager
config = ConfigManager()
print(f"[4/8] OK — config file: {config.filepath}", flush=True)

print("[5/8] SpeedMeterWidget...", flush=True)
from widget_window import SpeedMeterWidget
widget = SpeedMeterWidget(config_manager=config)
print(f"[5/8] OK — mode={widget.mode} pos=({widget.x()},{widget.y()}) size=({widget.width()}x{widget.height()})", flush=True)

print("[6/8] TrayManager...", flush=True)
from tray_manager import TrayManager
tray = TrayManager(config_manager=config)
print(f"[6/8] OK — tray visible={tray.tray_icon.isVisible()}", flush=True)

print("[7/8] NetworkMonitor...", flush=True)
from network_monitor import NetworkMonitor
monitor = NetworkMonitor(interval_ms=1000, nic_name="auto")
print("[7/8] OK", flush=True)

print("[8/8] Showing widget & starting monitor...", flush=True)
monitor.stats_updated.connect(lambda u,d,ts,tr,p: widget.update_stats(u,d,ts,tr,p))
monitor.start()
widget.show()
widget.raise_()

print(f"[8/8] DONE — widget.isVisible()={widget.isVisible()} widget geometry=({widget.x()},{widget.y()},{widget.width()},{widget.height()})", flush=True)
print(">>> App event loop starting. Close widget via tray to exit. <<<", flush=True)

# Run for 5 seconds then auto-exit for diagnosis
from PySide6.QtCore import QTimer
QTimer.singleShot(5000, lambda: (print("Auto-exit after 5s", flush=True), monitor.stop(), sm.detach(), app.quit()))
sys.exit(app.exec())
