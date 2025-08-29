import json
import shutil
from datetime import datetime
from typing import Dict
from .config import SNIPPETS_FILE, BACKUPS_DIR

def read_json(path) -> Dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def write_json_with_backup(path, data: Dict):
    # backup old
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, BACKUPS_DIR / f"{path.stem}_{ts}{path.suffix}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def import_snippets(file_path) -> Dict:
    return json.loads(file_path.read_text(encoding="utf-8"))

def export_snippets(file_path, data: Dict):
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")