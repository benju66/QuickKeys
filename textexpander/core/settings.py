import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List
from .config import SETTINGS_FILE

@dataclass
class Settings:
    enabled: bool = True
    expand_on_tab: bool = False
    trigger_prefix: str = "/"
    blacklist_process_names: List[str] = field(default_factory=lambda: ["keepass.exe", "1password.exe"])
    per_app_overrides: Dict[str, bool] = field(default_factory=dict)  # {"notepad.exe": True/False}
    logging_enabled: bool = False

    def save(self):
        SETTINGS_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return cls(**data)
            except Exception:
                pass
        s = cls()
        s.save()
        return s