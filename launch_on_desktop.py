import os
import sys
import win32file
import win32process
import win32security

_dir = os.path.dirname(os.path.abspath(__file__))
installed_exe = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Speed Meter\Speed Meter.exe")
extra_args = " ".join(sys.argv[1:])

if os.path.exists(installed_exe):
    cmd = f'"{installed_exe}" {extra_args}'.strip()
else:
    python_path = r"C:\Users\bram\AppData\Local\Programs\Python\Python312\pythonw.exe"
    main_py = os.path.join(_dir, "main.py")
    cmd = f'"{python_path}" "{main_py}" {extra_args}'.strip()

log_file = os.path.join(os.path.expanduser("~"), ".speed_meter", "app_output.log")

os.makedirs(os.path.dirname(log_file), exist_ok=True)

sa = win32security.SECURITY_ATTRIBUTES()
sa.bInheritHandle = True

h_out = win32file.CreateFile(
    log_file,
    win32file.GENERIC_WRITE,
    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
    sa,
    win32file.CREATE_ALWAYS,
    win32file.FILE_ATTRIBUTE_NORMAL,
    None
)

si = win32process.STARTUPINFO()
si.dwFlags |= win32process.STARTF_USESTDHANDLES
si.hStdOutput = h_out
si.hStdError = h_out
si.lpDesktop = r"WinSta0\Default"

try:
    hproc, hthread, pid, tid = win32process.CreateProcess(
        None,
        cmd,
        None,
        None,
        True,
        0,
        None,
        _dir,
        si
    )
    win32file.CloseHandle(h_out)
    print(f"Launched main.py on desktop with PID {pid}")
except Exception as e:
    win32file.CloseHandle(h_out)
    print(f"Error launching: {e}")
