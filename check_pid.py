import win32gui
import win32process

p = 50208
found = []
def cb(h, _):
    try:
        _, pid = win32process.GetWindowThreadProcessId(h)
        if pid == p:
            found.append((h, win32gui.GetWindowText(h), win32gui.GetClassName(h), win32gui.GetWindowRect(h), win32gui.IsWindowVisible(h)))
    except:
        pass

win32gui.EnumWindows(cb, None)
print(f"Found {len(found)} windows for PID {p}:")
for w in found:
    print(w)
