import winreg
from pathlib import Path
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "TextExpanderPy"

def get_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, APP_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except OSError:
        return False

def set_autostart_enabled(enable: bool):
    exe = sys.executable
    script = Path(sys.argv[0]).resolve()
    cmd = f'"{exe}" "{script}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enable:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
    except OSError:
        pass