import os
from pathlib import Path

APP_NAME = "TextExpanderPy"

APP_DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

SNIPPETS_FILE = APP_DATA_DIR / "snippets.json"
SETTINGS_FILE = APP_DATA_DIR / "settings.json"
BACKUPS_DIR = APP_DATA_DIR / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)

LOG_FILE = APP_DATA_DIR / "debug.log"

DEFAULT_SNIPPETS = {
    "sig": "Best regards,\nBen{cursor}",
    "addr": "Fendler Patterson Construction\nEden Prairie, MN{cursor}"
}