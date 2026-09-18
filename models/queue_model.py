from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QPixmap


class QueueItem:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.name = Path(filepath).name
        # Statuses: "waiting", "processing", "completed", "failed", "cancelled"
        self.status = "waiting"
        self.progress = 0       # 0 to 100
        self.thumbnail: Optional[QPixmap] = None
        self.error_msg: str = ""
        self.output_path: str = ""


class QueueModel(QAbstractListModel):
    FilepathRole = Qt.UserRole + 1
    StatusRole = Qt.UserRole + 2
    ProgressRole = Qt.UserRole + 3
    ThumbnailRole = Qt.UserRole + 4
    ErrorRole = Qt.UserRole + 5
    OutputPathRole = Qt.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[QueueItem] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.items)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
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
        elif role == self.ErrorRole:
            return item.error_msg
        elif role == self.OutputPathRole:
            return item.output_path
        return None

    def add_file(self, filepath: str) -> bool:
        for item in self.items:
            if item.filepath == filepath:
                return False
        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(QueueItem(filepath))
        self.endInsertRows()
        return True

    def remove_file(self, row: int) -> bool:
        if 0 <= row < len(self.items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self.items.pop(row)
            self.endRemoveRows()
            return True
        return False

    def clear(self) -> None:
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()

    def get_filepaths(self) -> List[str]:
        return [item.filepath for item in self.items]

    def reset_all_status(self) -> None:
        if not self.items:
            return
        for item in self.items:
            item.status = "waiting"
            item.progress = 0
            item.error_msg = ""
        self.dataChanged.emit(self.index(0), self.index(len(self.items) - 1), [self.StatusRole, self.ProgressRole])

    def update_file_status(
        self,
        filepath: str,
        progress: int,
        status: Optional[str] = None,
        error_msg: str = "",
        output_path: str = ""
    ) -> None:
        for i, item in enumerate(self.items):
            if item.filepath == filepath:
                item.progress = progress
                if status:
                    item.status = status
                if error_msg:
                    item.error_msg = error_msg
                if output_path:
                    item.output_path = output_path
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.ProgressRole, self.StatusRole, self.ErrorRole, self.OutputPathRole])
                break

    def set_thumbnail(self, row: int, pixmap: QPixmap) -> None:
        if 0 <= row < len(self.items):
            self.items[row].thumbnail = pixmap
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [self.ThumbnailRole])
