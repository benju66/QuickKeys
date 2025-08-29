from typing import Dict
from PyQt6 import QtCore, QtGui

class SnippetTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: Dict[str, str]):
        super().__init__()
        self._headers = ["Trigger (no leading /)", "Expansion (supports {cursor})"]
        self._rows = [(k, v) for k, v in data.items()]

    def rowCount(self, parent=None): return len(self._rows)
    def columnCount(self, parent=None): return 2

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        r, c = index.row(), index.column()
        key, val = self._rows[r]
        if role in (QtCore.Qt.ItemDataRole.DisplayRole, QtCore.Qt.ItemDataRole.EditRole):
            return key if c == 0 else val
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and " " in key and c == 0:
            return QtGui.QBrush(QtGui.QColor("red"))
        return None

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.ItemDataRole.DisplayRole: return None
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self._headers[section]
        return str(section + 1)

    def flags(self, index):
        if not index.isValid(): return QtCore.Qt.ItemFlag.NoItemFlags
        return (QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable)

    def setData(self, index, value, role):
        if role != QtCore.Qt.ItemDataRole.EditRole: return False
        r, c = index.row(), index.column()
        key, val = self._rows[r]
        if c == 0:
            self._rows[r] = (value.strip(), val)
        else:
            self._rows[r] = (key, value)
        self.dataChanged.emit(index, index)
        return True

    def add_row(self, trigger="", expansion=""):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._rows), len(self._rows))
        self._rows.append((trigger, expansion))
        self.endInsertRows()

    def remove_rows(self, rows: list):
        for r in sorted(rows, reverse=True):
            self.beginRemoveRows(QtCore.QModelIndex(), r, r)
            self._rows.pop(r)
            self.endRemoveRows()

    def to_dict(self) -> Dict[str, str]:
        out = {}
        for k, v in self._rows:
            k = k.strip()
            if k:
                out[k] = v
        return out

    def set_from_dict(self, data: Dict[str, str]):
        self.beginResetModel()
        self._rows = [(k, v) for k, v in data.items()]
        self.endResetModel()

    def filter(self, query: str):
        query = query.strip().lower()
        if not query:
            return
        # This is a UI helper; final filtering is done in window by setting model