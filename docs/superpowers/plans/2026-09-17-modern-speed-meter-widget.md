# Modern Windows Speed Meter Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a modern, high-performance, floating network speed meter widget for Windows with 3 switchable UI modes (Capsule Pill, Taskbar Bar, Glass Card), free drag-and-drop, dynamic snapping to the Windows taskbar near the Wi-Fi icon, a modern Fluent Settings dialog, and system tray integration.

**Architecture:** PySide6 (Qt 6) desktop application featuring a frameless, translucent, always-on-top window. Network telemetry is calculated in a background `QThread` via `psutil` delta byte counters and latency pings. Windows Shell geometry (`pywin32`) locates the Taskbar and System Tray notification area for pixel-accurate snapping near the Wi-Fi icon. Configurations are persisted in `settings.json`.

**Tech Stack:** Python 3.12, PySide6 (Qt 6.11.2), psutil 7.2.2, pywin32 312, pytest.

**Spec:** `docs/superpowers/specs/2026-09-17-modern-speed-meter-widget-design.md`

## Global Constraints
- Target OS: Windows 10 and Windows 11 (64-bit).
- Resource efficiency: Under 35 MB RAM, <0.2% CPU idle/active.
- DPI Scaling: Full support for high-DPI scaling (100%, 125%, 150%, 200%).
- Non-Admin Execution: All registry operations (startup) must strictly use `HKEY_CURRENT_USER`.
- UI/UX Design: Windows 11 Fluent aesthetic, dark frosted glass (`rgba(24, 24, 28, 0.88)`), subtle neon accents, crisp typography (Segoe UI Variable / Segoe UI).

---

### Task 1: Configuration Management System (`config_manager.py`)

**Files:**
- Create: `config_manager.py`
- Test: `tests/test_config_manager.py`

**Interfaces:**
- Consumes: Standard library `json`, `os`, `pathlib`
- Produces: `ConfigManager` class with methods:
  - `load() -> dict`
  - `save(config: dict) -> None`
  - `get(key: str, default: Any) -> Any`
  - `set(key: str, value: Any) -> None`
  - `get_all() -> dict`

- [ ] **Step 1: Write the failing test**

```python
import os
import pytest
from config_manager import ConfigManager

def test_config_defaults(tmp_path):
    config_file = tmp_path / "settings.json"
    cfg = ConfigManager(filepath=str(config_file))
    assert cfg.get("widget_mode") == "capsule"
    assert cfg.get("always_on_top") is True
    assert cfg.get("opacity") == 0.92
    assert cfg.get("up_color") == "#00E676"
    assert cfg.get("down_color") == "#00E5FF"

def test_config_save_and_reload(tmp_path):
    config_file = tmp_path / "settings.json"
    cfg = ConfigManager(filepath=str(config_file))
    cfg.set("pos_x", 500)
    cfg.set("pos_y", 800)
    cfg.set("widget_mode", "taskbar")
    
    cfg2 = ConfigManager(filepath=str(config_file))
    assert cfg2.get("pos_x") == 500
    assert cfg2.get("pos_y") == 800
    assert cfg2.get("widget_mode") == "taskbar"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_config_manager.py`
Expected: ModuleNotFoundError: No module named 'config_manager'

- [ ] **Step 3: Implement `config_manager.py`**

```python
import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG = {
    "pos_x": 100,
    "pos_y": 100,
    "widget_mode": "capsule",  # "capsule", "taskbar", "card"
    "always_on_top": True,
    "locked_position": False,
    "nic_name": "auto",
    "refresh_interval_ms": 1000,
    "opacity": 0.92,
    "theme": "dark_glass",
    "up_color": "#00E676",
    "down_color": "#00E5FF",
    "font_family": "Segoe UI Variable Display, Segoe UI, sans-serif",
    "font_size": 9,
    "autostart": False,
    "show_sparkline": True
}

class ConfigManager:
    def __init__(self, filepath: str = None):
        if filepath is None:
            base_dir = Path.home() / ".speed_meter"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.filepath = str(base_dir / "settings.json")
        else:
            self.filepath = filepath
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
        self.config: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    data = DEFAULT_CONFIG.copy()
                    data.update(saved)
                    return data
            except Exception:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        self.config[key] = value
        if auto_save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_config_manager.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**
`git add config_manager.py tests/test_config_manager.py`
`git commit -m "feat: implement configuration management system"`

---

### Task 2: Network Telemetry & Monitor Worker (`network_monitor.py`)

**Files:**
- Create: `network_monitor.py`
- Test: `tests/test_network_monitor.py`

**Interfaces:**
- Consumes: `psutil`, `PySide6.QtCore.QThread`, `PySide6.QtCore.Signal`
- Produces: `NetworkMonitor(QThread)`
  - Signal: `stats_updated(float up_bps, float down_bps, float total_sent, float total_recv, int ping_ms)`
  - Methods: `set_interval(ms: int)`, `set_nic(name: str)`, `get_available_nics() -> list[str]`, `format_speed(bytes_per_sec: float) -> str`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from network_monitor import NetworkMonitor

def test_format_speed():
    assert NetworkMonitor.format_speed(500) == "500 B/s"
    assert NetworkMonitor.format_speed(1024) == "1.00 KB/s"
    assert NetworkMonitor.format_speed(1024 * 1024 * 2.5) == "2.50 MB/s"
    assert NetworkMonitor.format_speed(1024 * 1024 * 1024 * 1.2) == "1.20 GB/s"

def test_get_available_nics():
    nics = NetworkMonitor.get_available_nics()
    assert isinstance(nics, list)
    assert "auto" in nics
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_network_monitor.py`
Expected: ModuleNotFoundError: No module named 'network_monitor'

- [ ] **Step 3: Implement `network_monitor.py`**

```python
import time
import socket
import psutil
from PySide6.QtCore import QThread, Signal

class NetworkMonitor(QThread):
    # up_bps, down_bps, total_sent, total_recv, ping_ms
    stats_updated = Signal(float, float, float, float, int)

    def __init__(self, interval_ms: int = 1000, nic_name: str = "auto", parent=None):
        super().__init__(parent)
        self.interval_sec = max(0.2, interval_ms / 1000.0)
        self.nic_name = nic_name
        self.running = True
        self.last_sent = 0
        self.last_recv = 0
        self.last_time = time.time()
        self.session_sent_start = 0
        self.session_recv_start = 0
        self._init_counters()

    def _init_counters(self):
        sent, recv = self._get_raw_counters()
        self.last_sent = sent
        self.last_recv = recv
        self.last_time = time.time()
        self.session_sent_start = sent
        self.session_recv_start = recv

    @staticmethod
    def get_available_nics() -> list[str]:
        nics = ["auto"]
        try:
            for name in psutil.net_if_addrs().keys():
                nics.append(name)
        except Exception:
            pass
        return nics

    def set_interval(self, ms: int):
        self.interval_sec = max(0.2, ms / 1000.0)

    def set_nic(self, name: str):
        self.nic_name = name
        self._init_counters()

    def _get_raw_counters(self) -> tuple[int, int]:
        try:
            if self.nic_name == "auto" or not self.nic_name:
                io = psutil.net_io_counters()
                return io.bytes_sent, io.bytes_recv
            else:
                per_nic = psutil.net_io_counters(pernic=True)
                if self.nic_name in per_nic:
                    io = per_nic[self.nic_name]
                    return io.bytes_sent, io.bytes_recv
                io = psutil.net_io_counters()
                return io.bytes_sent, io.bytes_recv
        except Exception:
            return 0, 0

    def _measure_ping(self) -> int:
        start = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            # Ping Cloudflare DNS 1.1.1.1 port 53 (DNS)
            s.connect(("1.1.1.1", 53))
            s.close()
            return int((time.time() - start) * 1000)
        except Exception:
            return -1

    def run(self):
        ping_counter = 0
        current_ping = -1
        while self.running:
            time.sleep(self.interval_sec)
            now = time.time()
            elapsed = now - self.last_time
            if elapsed <= 0:
                elapsed = 1.0

            sent, recv = self._get_raw_counters()
            up_rate = max(0.0, (sent - self.last_sent) / elapsed)
            down_rate = max(0.0, (recv - self.last_recv) / elapsed)

            self.last_sent = sent
            self.last_recv = recv
            self.last_time = now

            session_sent = max(0, sent - self.session_sent_start)
            session_recv = max(0, recv - self.session_recv_start)

            # Sample ping every 3 cycles
            ping_counter += 1
            if ping_counter >= 3:
                ping_counter = 0
                current_ping = self._measure_ping()

            self.stats_updated.emit(up_rate, down_rate, session_sent, session_recv, current_ping)

    def stop(self):
        self.running = False
        self.wait(2000)

    @staticmethod
    def format_speed(bytes_per_sec: float) -> str:
        if bytes_per_sec < 1000:
            return f"{int(bytes_per_sec)} B/s"
        elif bytes_per_sec < 1000 * 1000:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1000 * 1000 * 1000:
            return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"

    @staticmethod
    def format_bytes(total_bytes: float) -> str:
        if total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        elif total_bytes < 1024 * 1024 * 1024:
            return f"{total_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_network_monitor.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**
`git add network_monitor.py tests/test_network_monitor.py`
`git commit -m "feat: implement network telemetry monitor worker"`

---

### Task 3: Windows Integration & Taskbar Wi-Fi Snapping Engine (`win_utils.py`)

**Files:**
- Create: `win_utils.py`
- Test: `tests/test_win_utils.py`

**Interfaces:**
- Consumes: `win32gui`, `win32con`, `win32api`, `winreg`
- Produces:
  - `get_taskbar_position() -> dict` (rect, orientation: "bottom"|"top"|"left"|"right")
  - `get_tray_wifi_dock_coordinate(widget_width: int, widget_height: int) -> tuple[int, int]`
  - `set_windows_autostart(app_name: str, app_path: str, enable: bool) -> bool`
  - `is_windows_autostart_enabled(app_name: str) -> bool`

- [ ] **Step 1: Write test for win_utils**

```python
import pytest
from win_utils import get_taskbar_position, get_tray_wifi_dock_coordinate

def test_taskbar_detection():
    tb = get_taskbar_position()
    assert isinstance(tb, dict)
    assert "rect" in tb
    assert "orientation" in tb
    assert tb["orientation"] in ["bottom", "top", "left", "right"]

def test_dock_coordinate():
    x, y = get_tray_wifi_dock_coordinate(120, 36)
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert x > 0
    assert y > 0
```

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_win_utils.py`
Expected: ModuleNotFoundError: No module named 'win_utils'

- [ ] **Step 3: Implement `win_utils.py`**

```python
import sys
import winreg
import win32gui
import win32con
import win32api
from typing import Tuple, Dict, Any

APP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_taskbar_position() -> Dict[str, Any]:
    hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    if not hwnd:
        # Fallback to primary monitor bottom
        screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        return {
            "rect": (0, screen_h - 48, screen_w, screen_h),
            "orientation": "bottom",
            "hwnd": None
        }

    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    if width >= screen_w:
        orientation = "top" if top <= 0 else "bottom"
    else:
        orientation = "left" if left <= 0 else "right"

    return {
        "rect": rect,
        "orientation": orientation,
        "hwnd": hwnd
    }

def get_tray_wifi_dock_coordinate(widget_width: int, widget_height: int) -> Tuple[int, int]:
    tb = get_taskbar_position()
    tb_left, tb_top, tb_right, tb_bottom = tb["rect"]
    orientation = tb["orientation"]
    tb_hwnd = tb["hwnd"]

    tray_hwnd = win32gui.FindWindowEx(tb_hwnd, None, "TrayNotifyWnd", None) if tb_hwnd else None

    if tray_hwnd:
        tray_left, tray_top, tray_right, tray_bottom = win32gui.GetWindowRect(tray_hwnd)
        if orientation == "bottom":
            target_x = tray_left - widget_width - 8
            target_y = tb_top + max(0, (tb_bottom - tb_top - widget_height) // 2)
            return int(target_x), int(target_y)
        elif orientation == "top":
            target_x = tray_left - widget_width - 8
            target_y = tb_top + max(0, (tb_bottom - tb_top - widget_height) // 2)
            return int(target_x), int(target_y)

    # Fallback calculation
    if orientation == "bottom":
        target_x = tb_right - 260 - widget_width
        target_y = tb_top + max(0, (tb_bottom - tb_top - widget_height) // 2)
    elif orientation == "top":
        target_x = tb_right - 260 - widget_width
        target_y = tb_top + max(0, (tb_bottom - tb_top - widget_height) // 2)
    elif orientation == "left":
        target_x = tb_left + max(0, (tb_right - tb_left - widget_width) // 2)
        target_y = tb_bottom - 180 - widget_height
    else:  # right
        target_x = tb_left + max(0, (tb_right - tb_left - widget_width) // 2)
        target_y = tb_bottom - 180 - widget_height

    return int(target_x), int(target_y)

def set_windows_autostart(app_name: str, app_executable: str, enable: bool) -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG_KEY, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_executable}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to update autostart: {e}")
        return False

def is_windows_autostart_enabled(app_name: str) -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return bool(val)
    except FileNotFoundError:
        return False
    except Exception:
        return False
```

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_win_utils.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**
`git add win_utils.py tests/test_win_utils.py`
`git commit -m "feat: implement win32 taskbar geometry and autostart integration"`

---

### Task 4: Modern Fluent Design System & QSS Stylesheets (`styles.py`)

**Files:**
- Create: `styles.py`

**Interfaces:**
- Produces:
  - `get_capsule_style(bg_opacity: float, border_color: str) -> str`
  - `get_taskbar_style(bg_opacity: float) -> str`
  - `get_card_style(bg_opacity: float) -> str`
  - `get_settings_dialog_style() -> str`
  - `get_menu_style() -> str`

- [ ] **Step 1: Implement `styles.py`**
Include crisp styles for Capsule (Pill), Taskbar bar, Glass Card, Context Menus, and the Fluent Settings Dialog.

- [ ] **Step 2: Verify syntax via Python interpreter**
Run: `python -c "import styles; print(len(styles.get_settings_dialog_style()))"`
Expected: Prints stylesheet character count without syntax error.

- [ ] **Step 3: Commit**
`git add styles.py`
`git commit -m "feat: implement fluent glassmorphism styling and design tokens"`

---

### Task 5: Floating Speed Meter Widget Core with 3 Modes (`widget_window.py`)

**Files:**
- Create: `widget_window.py`

**Interfaces:**
- Consumes: `PySide6.QtWidgets.QWidget`, `config_manager.ConfigManager`, `styles.py`
- Produces: `SpeedMeterWidget(QWidget)`
  - Methods:
    - `update_stats(up_rate, down_rate, total_up, total_down, ping)`
    - `set_mode(mode: str)`: "capsule", "taskbar", "card"
    - `snap_to_taskbar()`
    - `toggle_lock()`
    - `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` (Drag & persistence)
    - `contextMenuEvent` (Right-click menu)

- [ ] **Step 1: Implement `widget_window.py` with multi-mode UI and drag logic**
Includes:
- Frameless, translucent background window.
- Smooth mouse drag handlers saving position on release.
- Dynamic layout generator switching seamlessly between:
  1. `Capsule Pill`: Sleek horizontal pill with neon upload/download arrows.
  2. `Taskbar Compact`: Super slim 2-line layout tailored for taskbar.
  3. `Glass Card`: Larger rounded card with sparkline history, ping badge, and total data usage.
- Sparkline painter widget rendering recent speed history in real-time.

- [ ] **Step 2: Test widget creation in headless/offscreen mode**
Run: `python -c "import sys; from PySide6.QtWidgets import QApplication; from widget_window import SpeedMeterWidget; app = QApplication(sys.argv); w = SpeedMeterWidget(); print(w.windowFlags()); app.quit()"`
Expected: Prints window flags containing FramelessWindowHint and WindowStaysOnTopHint.

- [ ] **Step 3: Commit**
`git add widget_window.py`
`git commit -m "feat: implement multi-mode floating speed meter widget"`

---

### Task 6: Windows System Tray Icon & Context Menu (`tray_manager.py`)

**Files:**
- Create: `tray_manager.py`

**Interfaces:**
- Consumes: `PySide6.QtWidgets.QSystemTrayIcon`, `PySide6.QtWidgets.QMenu`
- Produces: `TrayManager`
  - Signals/Callbacks: toggle visibility, open settings, snap to wifi, change mode, exit
  - Method: `update_tooltip(up_str: str, down_str: str)`
  - Generates dynamic high-res tray icon with upload/download arrows.

- [ ] **Step 1: Implement `tray_manager.py`**
- [ ] **Step 2: Verify tray manager module loads clean**
Run: `python -c "import sys; from PySide6.QtWidgets import QApplication; from tray_manager import TrayManager; app = QApplication(sys.argv); t = TrayManager(None); app.quit()"`
- [ ] **Step 3: Commit**
`git add tray_manager.py`
`git commit -m "feat: implement windows system tray manager and context menu"`

---

### Task 7: Modern Fluent Settings Dialog Window (`settings_dialog.py`)

**Files:**
- Create: `settings_dialog.py`

**Interfaces:**
- Consumes: `PySide6.QtWidgets.QDialog`, `config_manager.ConfigManager`, `network_monitor.NetworkMonitor`
- Produces: `SettingsDialog(QDialog)`
  - Emits: `settings_applied` signal
  - Tabs: General (Mode selection, Always on Top, Lock, Snap), Network (NIC picker, Refresh rate), Appearance (Color pickers, opacity slider, font picker), Startup (Windows boot toggle).

- [ ] **Step 1: Implement `settings_dialog.py`**
- [ ] **Step 2: Test settings dialog creation**
Run: `python -c "import sys; from PySide6.QtWidgets import QApplication; from settings_dialog import SettingsDialog; app = QApplication(sys.argv); d = SettingsDialog(); app.quit()"`
- [ ] **Step 3: Commit**
`git add settings_dialog.py`
`git commit -m "feat: implement modern fluent settings dialog window"`

---

### Task 8: Main Application Bootstrap & Live Verification (`main.py`)

**Files:**
- Create: `main.py`

**Interfaces:**
- Wires together `ConfigManager`, `NetworkMonitor`, `SpeedMeterWidget`, `TrayManager`, and `SettingsDialog`.
- Single-instance mutex check using QSharedMemory or Win32 mutex to prevent duplicate running instances.
- Graceful shutdown handling.

- [ ] **Step 1: Implement `main.py`**
- [ ] **Step 2: Run automated test suite**
Run: `python -m pytest tests/ -v`
Expected: All tests pass.
- [ ] **Step 3: Launch live verification run**
Run: `python main.py` in background, verify UI launches, test dragging, test snapping to Wi-Fi, test mode toggle, and verify clean exit.
- [ ] **Step 4: Commit**
`git add main.py`
`git commit -m "feat: complete application bootstrap and integration"`
