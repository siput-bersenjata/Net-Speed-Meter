import sys
import winreg
import win32gui
import win32con
import win32api
from typing import Tuple, Dict, Any

APP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_taskbar_position(screen=None) -> Dict[str, Any]:
    """
    Returns taskbar rectangle (left, top, right, bottom), orientation, and window handle.
    Supports both native Win32 window lookup and PySide6 screen geometry detection.
    """
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    # 1. Try PySide6 screen geometry if available
    try:
        if screen is None:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            avail = screen.availableGeometry()
            sw = geom.width()
            sh = geom.height()

            # Detect orientation and rect from available geometry
            if avail.top() > 0:
                # Taskbar at Top
                return {
                    "rect": (0, 0, sw, avail.top()),
                    "orientation": "top",
                    "hwnd": None
                }
            elif avail.height() < sh:
                # Taskbar at Bottom
                return {
                    "rect": (0, avail.height(), sw, sh),
                    "orientation": "bottom",
                    "hwnd": None
                }
            elif avail.left() > 0:
                # Taskbar at Left
                return {
                    "rect": (0, 0, avail.left(), sh),
                    "orientation": "left",
                    "hwnd": None
                }
            elif avail.width() < sw:
                # Taskbar at Right
                return {
                    "rect": (avail.width(), 0, sw, sh),
                    "orientation": "right",
                    "hwnd": None
                }
    except Exception:
        pass

    # 2. Try Win32 FindWindow
    hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    if hwnd and win32gui.IsWindow(hwnd):
        try:
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = right - left
            if width >= screen_w:
                orientation = "top" if top <= 0 else "bottom"
            else:
                orientation = "left" if left <= 0 else "right"
            return {
                "rect": rect,
                "orientation": orientation,
                "hwnd": hwnd
            }
        except Exception:
            pass

    # Fallback to standard bottom taskbar (48px high)
    return {
        "rect": (0, screen_h - 48, screen_w, screen_h),
        "orientation": "bottom",
        "hwnd": None
    }

def get_tray_wifi_dock_coordinate(widget_width: int, widget_height: int, screen=None) -> Tuple[int, int]:
    """
    Calculates the exact desktop coordinate to place the speed meter widget
    directly inside the Windows Taskbar immediately adjacent to the notification area
    (to the left of the '^' overflow chevron, Wi-Fi, audio, and battery icons).
    """
    tb = get_taskbar_position(screen=screen)
    tb_left, tb_top, tb_right, tb_bottom = tb["rect"]
    orientation = tb["orientation"]
    tb_hwnd = tb.get("hwnd")
    tb_height = tb_bottom - tb_top
    tb_width = tb_right - tb_left

    tray_hwnd = None
    if tb_hwnd:
        try:
            tray_hwnd = win32gui.FindWindowEx(tb_hwnd, None, "TrayNotifyWnd", None)
        except Exception:
            tray_hwnd = None

    if tray_hwnd and win32gui.IsWindow(tray_hwnd):
        try:
            t_left, t_top, t_right, t_bottom = win32gui.GetWindowRect(tray_hwnd)
            if orientation in ("bottom", "top"):
                # Position immediately to the left of the tray notification area with 6px spacing
                target_x = t_left - widget_width - 6
                target_y = tb_top + max(0, (tb_height - widget_height) // 2)
                return int(target_x), int(target_y)
            else:
                target_x = tb_left + max(0, (tb_width - widget_width) // 2)
                target_y = t_top - widget_height - 6
                return int(target_x), int(target_y)
        except Exception:
            pass

    # High-accuracy fallback based on typical Windows 10/11 system tray width
    # (Clock + Quick Settings + Tray Chevron occupy ~270px from the right edge)
    if orientation == "bottom":
        target_x = tb_right - 272 - widget_width
        target_y = tb_top + max(0, (tb_height - widget_height) // 2)
    elif orientation == "top":
        target_x = tb_right - 272 - widget_width
        target_y = tb_top + max(0, (tb_height - widget_height) // 2)
    elif orientation == "left":
        target_x = tb_left + max(0, (tb_width - widget_width) // 2)
        target_y = tb_bottom - 220 - widget_height
    else:  # right
        target_x = tb_left + max(0, (tb_width - widget_width) // 2)
        target_y = tb_bottom - 220 - widget_height

    return clamp_to_screen(int(target_x), int(target_y), widget_width, widget_height)

def clamp_to_screen(x: int, y: int, widget_width: int, widget_height: int) -> Tuple[int, int]:
    """Ensures coordinates are fully visible on the current primary screen without clipping."""
    try:
        screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    except Exception:
        screen_w, screen_h = 1920, 1080

    # Ensure widget is within horizontal boundaries
    if x < 4:
        x = 4
    elif x + widget_width > screen_w - 4:
        x = max(4, screen_w - widget_width - 4)

    # Ensure widget is within vertical boundaries (allow sitting in taskbar at bottom)
    if y < 2:
        y = 2
    elif y + widget_height > screen_h - 2:
        y = max(2, screen_h - widget_height - 2)

    return int(x), int(y)

def get_app_launch_command() -> str:
    """Returns the proper command line to launch Speed Meter silently in background."""
    import os
    if getattr(sys, 'frozen', False):
        return sys.executable
    
    # Python script mode - use pythonw.exe
    project_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(project_dir, "main.py")
    
    # Try finding pythonw.exe adjacent to python.exe
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable
        
    return f'"{pythonw}" "{main_py}"'

def set_windows_autostart(app_name: str, app_command: str = None, enable: bool = True) -> bool:
    """
    Sets or removes application entry in Windows CurrentVersion/Run registry
    AND creates/removes a shortcut in the Windows Startup folder for 100% startup reliability.
    """
    import os
    if not app_command:
        app_command = get_app_launch_command()

    # 1. Update Registry
    reg_ok = False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG_KEY, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_command)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        reg_ok = True
    except Exception as e:
        print(f"[win_utils] Failed to update autostart registry: {e}")

    # 2. Update Startup Folder Shortcut
    try:
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        startup_lnk = os.path.join(startup_dir, f"{app_name}.lnk")
        if enable:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(startup_lnk)
            if getattr(sys, 'frozen', False):
                shortcut.TargetPath = sys.executable
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            else:
                project_dir = os.path.dirname(os.path.abspath(__file__))
                py_dir = os.path.dirname(sys.executable)
                pythonw = os.path.join(py_dir, "pythonw.exe")
                shortcut.TargetPath = pythonw if os.path.exists(pythonw) else sys.executable
                shortcut.Arguments = f'"{os.path.join(project_dir, "main.py")}"'
                shortcut.WorkingDirectory = project_dir
                
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            shortcut.Save()
        else:
            if os.path.exists(startup_lnk):
                os.remove(startup_lnk)
    except Exception as e:
        print(f"[win_utils] Startup shortcut update note: {e}")

    return reg_ok

def is_windows_autostart_enabled(app_name: str) -> bool:
    """Checks whether application entry exists in Windows Run registry or Startup folder."""
    import os
    # Check Registry
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_REG_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        if val:
            return True
    except Exception:
        pass

    # Check Startup Folder
    try:
        startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
        startup_lnk = os.path.join(startup_dir, f"{app_name}.lnk")
        if os.path.exists(startup_lnk):
            return True
    except Exception:
        pass

    return False

def set_click_through_native(hwnd: int, enable: bool) -> bool:
    """
    Sets or removes the WS_EX_TRANSPARENT extended window style on Windows.
    When enabled, mouse clicks and hit-tests pass directly through the window
    to whatever is behind it (taskbar, desktop, icons, buttons).
    """
    if not hwnd:
        return False
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            new_style = ex_style | win32con.WS_EX_TRANSPARENT
        else:
            new_style = ex_style & ~win32con.WS_EX_TRANSPARENT
        if new_style != ex_style:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
        return True
    except Exception as e:
        print(f"[win_utils] Error setting native click-through on hwnd {hwnd}: {e}")
        return False
