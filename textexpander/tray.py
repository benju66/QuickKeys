from PyQt6 import QtGui, QtWidgets
from .core.autostart import get_autostart_enabled, set_autostart_enabled

def create_tray(app, manager_window, engine, settings):
    tray = QtWidgets.QSystemTrayIcon()
    tray.setToolTip("TextExpanderPy")
    tray.setIcon(app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))

    menu = QtWidgets.QMenu()

    toggle_action = QtGui.QAction("Enabled ✔" if settings.enabled else "Enabled ✖")
    def toggle_enabled():
        settings.enabled = not settings.enabled
        settings.save()
        toggle_action.setText("Enabled ✔" if settings.enabled else "Enabled ✖")
    toggle_action.triggered.connect(toggle_enabled)
    menu.addAction(toggle_action)

    menu.addSeparator()

    open_manager = QtGui.QAction("Open Snippet Manager")
    open_manager.triggered.connect(lambda: (manager_window.reload_models(), manager_window.show(), manager_window.raise_()))
    menu.addAction(open_manager)

    reload_engine = QtGui.QAction("Reload snippets (Ctrl+Alt+R)")
    reload_engine.triggered.connect(engine.reload_snippets)
    menu.addAction(reload_engine)

    menu.addSeparator()

    # Start with Windows
    startup_action = QtGui.QAction("Start with Windows")
    startup_action.setCheckable(True)
    startup_action.setChecked(get_autostart_enabled())
    def toggle_startup():
        set_autostart_enabled(startup_action.isChecked())
    startup_action.triggered.connect(toggle_startup)
    menu.addAction(startup_action)

    # Logging toggle
    log_action = QtGui.QAction("Enable logging")
    log_action.setCheckable(True)
    log_action.setChecked(settings.logging_enabled)
    def toggle_log():
        settings.logging_enabled = log_action.isChecked()
        settings.save()
    log_action.triggered.connect(toggle_log)
    menu.addAction(log_action)

    menu.addSeparator()

    quit_action = QtGui.QAction("Quit")
    quit_action.triggered.connect(QtWidgets.QApplication.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: manager_window.show() if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger else None)
    return tray