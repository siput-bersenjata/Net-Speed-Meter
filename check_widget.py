import ctypes
import ctypes.wintypes
import psutil

user32 = ctypes.windll.user32

python_pids = set()
for proc in psutil.process_iter(['pid', 'name']):
    if 'python' in proc.info['name'].lower():
        python_pids.add(proc.info['pid'])

print(f"Python PIDs: {python_pids}")

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

found = []

def enum_cb(hwnd, lparam):
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value in python_pids:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        cls = buf.value
        
        title_buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title_buf, 256)
        title = title_buf.value
        
        vis = user32.IsWindowVisible(hwnd)
        
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        print(f"  hwnd={hwnd} class={cls} title='{title}' visible={vis} rect=({rect.left},{rect.top},{rect.right},{rect.bottom}) pid={pid.value}")
    return True

user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
