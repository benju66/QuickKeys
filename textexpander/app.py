import sys
import threading
from PyQt6 import QtWidgets
from .core.settings import Settings
from .core.snippets import SnippetRepository
from .core.expander import ExpanderEngine
from .core.logger import get_logger
from .tray import create_tray
from .ui.main_window import SnippetManagerWindow

def run_app():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("TextExpanderPy")
    # Keep running in tray even if all windows are closed
    app.setQuitOnLastWindowClosed(False)

    logger = get_logger()
    settings = Settings.load()
    repo = SnippetRepository.load_or_create()

    # Expander runs in background thread
    engine = ExpanderEngine(settings=settings, repository=repo, logger=logger)
    t = threading.Thread(target=engine.run, daemon=True)
    t.start()

    # Manager window (created on demand from tray)
    manager = SnippetManagerWindow(settings, repo, engine, logger)
    # Show main window on startup
    manager.show()
    manager.raise_()
    manager.activateWindow()

    tray = create_tray(app, manager, engine, settings)
    tray.show()

    sys.exit(app.exec())