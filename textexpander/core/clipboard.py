from contextlib import contextmanager
import pyperclip

@contextmanager
def preserve_clipboard():
    try:
        original = pyperclip.paste()
    except Exception:
        original = None
    try:
        yield
    finally:
        if original is not None:
            try:
                pyperclip.copy(original)
            except Exception:
                pass