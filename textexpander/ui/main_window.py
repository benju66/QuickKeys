from PyQt6 import QtWidgets, QtCore
from pathlib import Path
from ..core.settings import Settings
from ..core.snippets import SnippetRepository
from ..core.storage import import_snippets, export_snippets
from ..core.config import SNIPPETS_FILE
from ..core.app_detector import get_foreground_process_name
from .models import SnippetTableModel
import psutil
import pyperclip

class SnippetManagerWindow(QtWidgets.QMainWindow):
    def __init__(self, settings: Settings, repo: SnippetRepository, engine, logger):
        super().__init__()
        self.setWindowTitle("TextExpanderPy – Snippet Manager")
        self.resize(820, 520)
        self.settings = settings
        self.repo = repo
        self.engine = engine
        self.logger = logger

        tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(tabs)

        # --- Snippets Tab
        self.model = SnippetTableModel(self.repo.all())

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked |
                                   QtWidgets.QAbstractItemView.EditTrigger.SelectedClicked)

        add_btn = QtWidgets.QPushButton("Add")
        del_btn = QtWidgets.QPushButton("Delete")
        save_btn = QtWidgets.QPushButton("Save")
        import_btn = QtWidgets.QPushButton("Import JSON…")
        export_btn = QtWidgets.QPushButton("Export JSON…")
        from_clip_btn = QtWidgets.QPushButton("New from Clipboard")

        add_btn.clicked.connect(lambda: self.model.add_row("", ""))

        del_btn.clicked.connect(self._delete_selected)
        save_btn.clicked.connect(self._save)
        import_btn.clicked.connect(self._import)
        export_btn.clicked.connect(self._export)
        from_clip_btn.clicked.connect(self._new_from_clipboard)

        search = QtWidgets.QLineEdit()
        search.setPlaceholderText("Search triggers or text…")
        search.textChanged.connect(self._apply_search)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(from_clip_btn)
        btn_row.addWidget(import_btn)
        btn_row.addWidget(export_btn)
        btn_row.addWidget(save_btn)

        snip_layout = QtWidgets.QVBoxLayout()
        snip_layout.addWidget(search)
        snip_layout.addWidget(self.table)
        snip_layout.addLayout(btn_row)

        snip_tab = QtWidgets.QWidget()
        snip_tab.setLayout(snip_layout)
        tabs.addTab(snip_tab, "Snippets")

        # --- Settings Tab
        settings_tab = self._build_settings_tab()
        tabs.addTab(settings_tab, "Settings")

        # Status bar
        self.statusBar().showMessage(f"Snippets file: {SNIPPETS_FILE}")

    # ---- UI Builders
    def _build_settings_tab(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        enabled_cb = QtWidgets.QCheckBox("Enable expansion")
        enabled_cb.setChecked(self.settings.enabled)
        enabled_cb.toggled.connect(self._toggle_enabled)

        tab_cb = QtWidgets.QCheckBox("Expand on Tab (instead of waiting for space/enter)")
        tab_cb.setChecked(self.settings.expand_on_tab)
        tab_cb.toggled.connect(self._toggle_expand_on_tab)

        trigger_label = QtWidgets.QLabel("Trigger prefix:")
        trigger_edit = QtWidgets.QLineEdit(self.settings.trigger_prefix)
        trigger_edit.setMaxLength(3)
        trigger_edit.setFixedWidth(80)
        trigger_edit.editingFinished.connect(lambda: self._set_trigger_prefix(trigger_edit.text().strip() or "/"))

        # Blacklist edit
        bl_label = QtWidgets.QLabel("Blacklist process names (comma-separated, e.g., keepass.exe, 1password.exe)")
        bl_edit = QtWidgets.QLineEdit(", ".join(self.settings.blacklist_process_names))
        bl_edit.editingFinished.connect(lambda: self._save_blacklist(bl_edit.text()))

        # Per-app enable/disable
        apps_label = QtWidgets.QLabel("Per-app overrides (checked = enabled, unchecked = disabled)")
        self.apps_list = QtWidgets.QListWidget()
        self.apps_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        refresh_apps = QtWidgets.QPushButton("Load running apps")
        refresh_apps.clicked.connect(self._load_running_apps)
        save_apps = QtWidgets.QPushButton("Save overrides")
        save_apps.clicked.connect(self._save_per_app_overrides)

        # Logging toggle
        log_cb = QtWidgets.QCheckBox("Enable logging")
        log_cb.setChecked(self.settings.logging_enabled)
        log_cb.toggled.connect(self._toggle_logging)

        # Active app hint
        active_btn = QtWidgets.QPushButton("Use current foreground app")
        active_btn.clicked.connect(self._add_current_app)

        layout.addWidget(enabled_cb)
        layout.addWidget(tab_cb)
        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(trigger_label)
        hl.addWidget(trigger_edit)
        hl.addStretch()
        layout.addLayout(hl)

        layout.addWidget(bl_label)
        layout.addWidget(bl_edit)

        layout.addSpacing(8)
        layout.addWidget(apps_label)
        layout.addWidget(self.apps_list)

        hl2 = QtWidgets.QHBoxLayout()
        hl2.addWidget(refresh_apps)
        hl2.addWidget(active_btn)
        hl2.addStretch()
        hl2.addWidget(save_apps)
        layout.addLayout(hl2)

        layout.addSpacing(8)
        layout.addWidget(log_cb)
        layout.addStretch()
        self._populate_per_app_list()
        return w

    # ---- Slots / Handlers
    def reload_models(self):
        self.model.set_from_dict(self.repo.all())

    def _apply_search(self, text: str):
        filtered = self.repo.search(text)
        self.model.set_from_dict(filtered)

    def _delete_selected(self):
        sel = self.table.selectionModel().selectedRows()
        rows = [i.row() for i in sel]
        self.model.remove_rows(rows)

    def _save(self):
        data = self.model.to_dict()
        # Duplicate guard (by nature of dict, but check user mistakes)
        if any(" " in k for k in data.keys()):
            QtWidgets.QMessageBox.warning(self, "Invalid triggers", "Triggers cannot contain spaces.")
            return
        self.repo.set_all(data)
        self.repo.save()
        self.statusBar().showMessage("Saved (with automatic backup). Press Ctrl+Alt+R to reload in background.", 5000)

    def _import(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import snippets", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            data = import_snippets(Path(path))
            self.model.set_from_dict(data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import failed", str(e))

    def _export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export snippets", "snippets_export.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            export_snippets(Path(path), self.model.to_dict())
            self.statusBar().showMessage("Exported.", 4000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export failed", str(e))

    def _new_from_clipboard(self):
        try:
            text = pyperclip.paste() or ""
        except Exception:
            text = ""
        self.model.add_row("", text)

    def _toggle_enabled(self, state: bool):
        self.settings.enabled = state
        self.settings.save()

    def _toggle_expand_on_tab(self, state: bool):
        self.settings.expand_on_tab = state
        self.settings.save()
        QtWidgets.QMessageBox.information(self, "Restart hook", "Toggle will take effect next launch.")

    def _toggle_logging(self, state: bool):
        self.settings.logging_enabled = state
        self.settings.save()

    def _set_trigger_prefix(self, prefix: str):
        self.settings.trigger_prefix = prefix[0] if prefix else "/"
        self.settings.save()

    def _save_blacklist(self, txt: str):
        parts = [p.strip().lower() for p in txt.split(",") if p.strip()]
        self.settings.blacklist_process_names = parts
        self.settings.save()

    def _populate_per_app_list(self):
        self.apps_list.clear()
        # Load existing overrides
        for name, enabled in sorted(self.settings.per_app_overrides.items()):
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked)
            self.apps_list.addItem(item)

    def _load_running_apps(self):
        names = set()
        for p in psutil.process_iter(attrs=['name']):
            try:
                names.add((p.info['name'] or "").lower())
            except Exception:
                pass
        # Merge into overrides (default True)
        for n in sorted(n for n in names if n):
            if n not in self.settings.per_app_overrides:
                self.settings.per_app_overrides[n] = True
        self._populate_per_app_list()

    def _save_per_app_overrides(self):
        overrides = {}
        for i in range(self.apps_list.count()):
            item = self.apps_list.item(i)
            overrides[item.text()] = item.checkState() == QtCore.Qt.CheckState.Checked
        self.settings.per_app_overrides = overrides
        self.settings.save()
        self.statusBar().showMessage("Per-app overrides saved.", 3000)

    def _add_current_app(self):
        name = get_foreground_process_name()
        if not name:
            return
        self.settings.per_app_overrides[name] = True
        self.settings.save()
        self._populate_per_app_list()