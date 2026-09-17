# Design Specification: Modern Windows Floating Speed Meter Widget

## 1. Overview & Objective
Build a lightweight, highly responsive, and aesthetically modern network speed monitoring widget for Windows. The application replaces outdated speed monitors with a Windows 11 Fluent Design inspired interface supporting:
- Free-floating drag-and-drop capability anywhere across multi-monitor setups.
- Dynamic "Snap to Taskbar (near Wi-Fi/System Tray)" positioning.
- Three switchable widget layouts: **Capsule Pill**, **Taskbar Compact Bar**, and **Floating Glass Card**.
- Real-time network telemetry (Upload/Download throughput, Ping/Latency, Session Data Usage).
- Low resource footprint (under 30 MB RAM, <0.2% CPU).
- Modern Settings Dialog and Windows System Tray integration.

## 2. Technology Stack & Dependencies
- **Runtime**: Python 3.12+ (64-bit on Windows)
- **GUI Toolkit**: PySide6 6.11.2 (Qt 6)
  - `Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool`
  - Translucent background with high DPI crisp rendering
- **System Telemetry**: `psutil 7.2.2` (per-NIC I/O counters, interface status)
- **OS Integration**: `pywin32` (`win32gui`, `win32con`, `win32api`) for Windows Taskbar (`Shell_TrayWnd`) detection and tray area geometry calculation.
- **Config Storage**: JSON (`settings.json`) in user local app directory or workspace.

## 3. Architecture & Components

```
Speed meter/
├── main.py                # Application bootstrap, single-instance enforcement, lifecycle
├── config_manager.py      # Reads/writes user preferences & persistent coordinates to settings.json
├── network_monitor.py     # Background QThread for non-blocking network sampling and ping
├── widget_window.py       # Main frameless widget with drag handlers & 3 swappable view modes
├── settings_dialog.py     # Modern Fluent-styled configuration window
├── tray_manager.py        # System tray icon with context menu
├── win_utils.py           # Win32 helpers for Taskbar geometry & Windows startup registry
└── styles.py              # Modern dark/light glassmorphism QSS stylesheets and color palettes
```

### Component Details

#### 3.1 `network_monitor.py` (Network Telemetry Worker)
- Runs as a `QThread` with configurable sample intervals (default: 1000ms / 1s).
- Emits Qt signal `stats_updated(float upload_bps, float download_bps, float total_sent, float total_recv, int ping_ms)`.
- Automatic Network Interface Card (NIC) detection:
  - Scans `psutil.net_if_stats()` for active, connected interfaces.
  - Automatically filters out virtual/loopback adapters unless selected.
  - Supports manual override to bind to a specific NIC (e.g., Wi-Fi, Ethernet).
- Lightweight ICMP or TCP ping to reliable endpoints (e.g., `1.1.1.1` or default gateway) to report connection latency.

#### 3.2 `widget_window.py` (Floating & Dockable Widget)
- **Window Flags**:
  - `FramelessWindowHint`: Removes default OS title bar and borders.
  - `WindowStaysOnTopHint`: Keeps widget above other windows.
  - `Tool`: Prevents appearing as an extra app icon in Alt+Tab or taskbar application list.
  - `WA_TranslucentBackground`: Enables true rounded corners and acrylic/frosted glass aesthetics.
- **Drag & Interaction**:
  - Left Mouse Press & Move: Moves the widget freely across the screen.
  - Left Mouse Release: Persists `(x, y)` to `settings.json`.
  - Right Click: Triggers a custom dark-mode styled `QMenu`.
  - Double Click: Opens the Settings window.
- **Three Switchable Modes**:
  1. **Capsule Pill**: Rounded pill (~140x36px), dark frosted glass (`rgba(24, 24, 28, 0.88)`), border `1px solid rgba(255,255,255,0.15)`, upload arrow `▲` (Neon Cyan/Emerald) & download arrow `▼` (Neon Green/Amber), crisp dynamic unit formatting (`KB/s`, `MB/s`, `GB/s`).
  2. **Taskbar Compact Bar**: Slim rectangle (~110x32px or ~120x36px) styled to match Windows 10/11 taskbar dark theme. Two compact rows designed to sit cleanly in the taskbar right next to the system tray icons.
  3. **Floating Glass Card**: Larger card (~190x85px) featuring Upload & Download speeds, a mini 20-point historical sparkline chart, ping latency badge, and total session data usage.

#### 3.3 `win_utils.py` (Taskbar & Wi-Fi Snapping Engine)
- Uses `win32gui.FindWindow("Shell_TrayWnd", None)` to inspect the Windows Taskbar location (Bottom, Top, Left, Right) and bounding rectangle.
- Finds child window `"TrayNotifyWnd"` to locate the system tray notification icon area (where Wi-Fi, Audio, Battery reside).
- Calculates target coordinate:
  - For standard bottom taskbar: places widget immediately to the left of `TrayNotifyWnd`, vertically centered within the taskbar height.
  - Handles multi-monitor primary screen coordinates properly.
- Provides `set_run_at_startup(bool)` using Windows Registry `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`.

#### 3.4 `settings_dialog.py` (Modern Settings UI)
- Category Tabs / Sections:
  - **General**: Widget Style (Pill / Taskbar Bar / Glass Card), Always on Top, Lock Position, Snap to Taskbar.
  - **Network**: Adapter Selection (Auto / specific Wi-Fi / Ethernet), Update Interval (0.5s, 1s, 2s), Unit Format (Auto, KB/s, MB/s).
  - **Appearance**: Theme (Dark Glass / Light Glass / Stealth), Custom Upload/Download accent colors, Font size, Opacity slider (50% - 100%).
  - **Startup**: Launch on Windows startup toggle.
- Clean Modern Fluent UI with rounded inputs, styled toggle switches, and real-time preview.

#### 3.5 `tray_manager.py` (System Tray Icon)
- Houses a clean network activity icon in the Windows notification tray.
- Tooltip displays current Upload / Download speeds and active NIC.
- Context Menu:
  - Toggle Widget Visibility (Show / Hide)
  - Snap to Wi-Fi / Taskbar
  - Switch Widget Style (Pill / Taskbar / Card)
  - Lock / Unlock Position
  - Open Settings
  - Exit

#### 3.6 `config_manager.py` (Configuration & State Persistence)
- Reads/writes `settings.json` with fallback defaults.
- Stores:
  - `pos_x`, `pos_y`
  - `widget_mode`: `"capsule"`, `"taskbar"`, `"card"`
  - `always_on_top`: `true`
  - `locked_position`: `false`
  - `nic_name`: `"auto"`
  - `refresh_interval_ms`: `1000`
  - `opacity`: `0.92`
  - `theme`: `"dark_glass"`
  - `up_color`: `"#00E676"`
  - `down_color`: `"#00E5FF"`
  - `autostart`: `false`

## 4. Error Handling & Edge Cases
- **Network Interface Disconnect**: Gracefully falls back to zero transfer rate without exceptions; continuously checks for newly active interfaces.
- **Taskbar Relocation / Screen Resolution Change**: Re-validates position on screen changes to ensure widget does not drift off-screen.
- **Non-Admin Execution**: All configurations and registry startup entries use `HKEY_CURRENT_USER`, avoiding UAC elevation prompts.

## 5. Verification & Testing
- Automated test script to verify `network_monitor.py` metrics collection and `config_manager.py` read/write cycles.
- Manual verification on live Windows desktop:
  1. Free dragging and persistence across restarts.
  2. "Snap to Wi-Fi" accuracy on the taskbar.
  3. Seamless switching between Capsule Pill, Taskbar Bar, and Glass Card.
  4. Context menu actions and Settings dialog changes applying immediately.
