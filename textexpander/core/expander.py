import time
import threading
import keyboard  # global hooks
import pyperclip
from typing import Optional
from .settings import Settings
from .snippets import SnippetRepository
from .clipboard import preserve_clipboard
from .app_detector import get_foreground_process_name, get_foreground_window_title

class ExpanderEngine:
    def __init__(self, settings: Settings, repository: SnippetRepository, logger=None):
        self.settings = settings
        self.repo = repository
        self.logger = logger
        self._buffer = ""  # chars since last boundary
        self._lock = threading.Lock()
        self._running = True

    # ---- Public controls
    def run(self):
        # Hotkeys
        keyboard.add_hotkey('ctrl+alt+e', self.toggle_enabled)
        keyboard.add_hotkey('ctrl+alt+r', self.reload_snippets)
        keyboard.add_hotkey('ctrl+alt+z', lambda: keyboard.send('ctrl+z'))  # undo

        # Optional: Expand on Tab (suppressed)
        if self.settings.expand_on_tab:
            keyboard.add_hotkey('tab', self._on_tab, suppress=True)

        keyboard.hook(self._on_key_event)
        if self.logger and self.settings.logging_enabled:
            self.logger.info("Expander started")
        try:
            while self._running:
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass

    def stop(self):
        self._running = False

    def toggle_enabled(self):
        self.settings.enabled = not self.settings.enabled
        self.settings.save()
        if self.logger and self.settings.logging_enabled:
            self.logger.info(f"enabled={self.settings.enabled}")

    def reload_snippets(self):
        with self._lock:
            self.repo.set_all(self.repo.all())  # noop, API symmetry
        if self.logger and self.settings.logging_enabled:
            self.logger.info("snippets reloaded (from memory)")

    # ---- Core hook handlers
    def _on_key_event(self, event):
        if not self.settings.enabled or event.event_type != 'down':
            return

        # Respect per-app settings / blacklists
        if not self._allowed_in_foreground_app():
            self._buffer = ""
            return

        name = event.name

        # boundaries -> attempt expansion then reset
        if name in ('space', 'enter') or (len(name) == 1 and not name.isalnum()):
            self._try_expand(boundary=True)
            self._buffer = ""
            return

        if name == 'tab':
            # If expand_on_tab is True, _on_tab handles it; here just buffer logic for normal flow
            self._buffer += '\t'
            return

        if name == 'backspace':
            self._buffer = self._buffer[:-1]
            return

        if len(name) == 1:
            self._buffer += name
            # lightweight lazy check (no delete/paste here)
            self._try_expand(boundary=False)

    def _on_tab(self):
        # Suppressed TAB: if trigger matches, expand and swallow; otherwise pass through a real Tab
        if not self.settings.enabled:
            keyboard.send('tab')
            return
        if not self._allowed_in_foreground_app():
            keyboard.send('tab')
            return

        if self._buffer.startswith(self.settings.trigger_prefix):
            trigger = self._buffer[len(self.settings.trigger_prefix):]
            if trigger and self.repo.get(trigger) is not None:
                self._do_expand(trigger, consumed_chars=len(self._buffer))
                self._buffer = ""
                return
        # no match -> send a real Tab to compensate for suppression
        keyboard.send('tab')

    # ---- Expansion helpers
    def _try_expand(self, boundary: bool):
        if not self._buffer.startswith(self.settings.trigger_prefix):
            return
        trigger = self._buffer[len(self.settings.trigger_prefix):]
        if not trigger:
            return
        text = self.repo.get(trigger)
        if text is None:
            return
        # On boundary or lazy? Only expand on boundary unless expand_on_tab is enabled (handled separately)
        if boundary:
            self._do_expand(trigger, consumed_chars=len(self._buffer))

    def _do_expand(self, trigger: str, consumed_chars: int):
        # Delete the typed trigger first
        for _ in range(consumed_chars):
            keyboard.send('backspace')

        expansion = self.repo.get(trigger) or ""
        # Handle {cursor} placeholder: compute post length (characters to move back)
        pre, post = _split_cursor(expansion)
        combined = pre + post
        with preserve_clipboard():
            pyperclip.copy(combined)
            keyboard.send('ctrl+v')
        post_len = len(post)
        if post_len > 0:
            # Move caret left N times to land at {cursor} position
            for _ in range(post_len):
                keyboard.send('left')

    # ---- Policy helpers
    def _allowed_in_foreground_app(self) -> bool:
        proc = get_foreground_process_name()
        title = get_foreground_window_title().lower()
        # Blacklist by process
        if proc in (p.lower() for p in self.settings.blacklist_process_names):
            return False
        # Per-app overrides (False disables, True forces enable)
        if proc in self.settings.per_app_overrides:
            return bool(self.settings.per_app_overrides[proc])
        # crude password/title check
        if "password" in title or "signin" in title or "login" in title:
            return False
        return True

def _split_cursor(text: str) -> tuple[str, str]:
    token = "{cursor}"
    idx = text.find(token)
    if idx == -1:
        return text, ""
    pre = text[:idx]
    post = text[idx + len(token):]
    return pre, post