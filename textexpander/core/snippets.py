from typing import Dict, List, Tuple, Optional
from .config import SNIPPETS_FILE, DEFAULT_SNIPPETS
from .storage import read_json, write_json_with_backup

class SnippetRepository:
    def __init__(self, data: Dict[str, str]):
        self._data = dict(data)

    @classmethod
    def load_or_create(cls):
        if not SNIPPETS_FILE.exists():
            write_json_with_backup(SNIPPETS_FILE, DEFAULT_SNIPPETS)
        return cls(read_json(SNIPPETS_FILE))

    def all(self) -> Dict[str, str]:
        return dict(self._data)

    def set_all(self, data: Dict[str, str]):
        self._data = dict(data)

    def save(self):
        write_json_with_backup(SNIPPETS_FILE, self._data)

    def validate(self) -> Tuple[bool, List[str]]:
        dups = [k for k in self._data.keys() if list(self._data.keys()).count(k) > 1]
        # (dict can't hold dup keys; guard for UI)
        bad = [k for k in self._data if " " in k or not k]
        # return "invalid" if any bad keys
        return (len(bad) == 0, bad)

    def search(self, text: str) -> Dict[str, str]:
        text = text.strip().lower()
        if not text:
            return self.all()
        return {k: v for k, v in self._data.items() if text in k.lower() or text in v.lower()}

    def get(self, trigger: str) -> Optional[str]:
        return self._data.get(trigger)

    def contains_trigger(self, trigger: str) -> bool:
        return trigger in self._data