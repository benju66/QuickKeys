import ctypes
import ctypes.wintypes as wt
import psutil

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def get_foreground_window_title() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return buf.value or ""

def get_foreground_process_name() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        p = psutil.Process(pid.value)
        return (p.name() or "").lower()
    except Exception:
        return ""