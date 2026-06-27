from pathlib import Path
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex


class QueueItem:
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = Path(filepath).name
        self.status = "pending" # pending, processing, success, failed
        self.progress = 0       # 0 to 100
        self.thumbnail = None


class QueueModel(QAbstractListModel):
    FilepathRole = Qt.UserRole + 1
    StatusRole = Qt.UserRole + 2
    ProgressRole = Qt.UserRole + 3
    ThumbnailRole = Qt.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None
        item = self.items[index.row()]
        if role == Qt.DisplayRole:
            return item.name
        elif role == self.FilepathRole:
            return item.filepath
        elif role == self.StatusRole:
            return item.status
        elif role == self.ProgressRole:
            return item.progress
        elif role == self.ThumbnailRole:
            return item.thumbnail
        return None

    def add_file(self, filepath):
        for item in self.items:
            if item.filepath == filepath:
                return False
        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(QueueItem(filepath))
        self.endInsertRows()
        return True

    def remove_file(self, row):
        if 0 <= row < len(self.items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.items.pop(row)
            self.endRemoveRows()
            return True
        return False

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()

    def update_progress(self, filepath, progress, status=None):
        for i, item in enumerate(self.items):
            if item.filepath == filepath:
                item.progress = progress
                if status:
                    item.status = status
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.ProgressRole, self.StatusRole])
                break

    def set_thumbnail(self, row, pixmap):
        if 0 <= row < len(self.items):
            self.items[row].thumbnail = pixmap
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [self.ThumbnailRole])