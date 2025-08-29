import logging
from .config import LOG_FILE

_logger = None

def get_logger():
    global _logger
    if _logger:
        return _logger
    logger = logging.getLogger("TextExpanderPy")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    _logger = logger
    return logger