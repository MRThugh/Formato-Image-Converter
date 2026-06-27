from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import (
    QLabel, QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QStyledItemDelegate, QStyle
)
from PySide6.QtGui import QPainter, QColor, QPen, QCursor, QWheelEvent
from models.queue_model import QueueModel


class ClickableLabel(QLabel):
    double_clicked = Signal()
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_anim = None

    def wheelEvent(self, event: QWheelEvent):
        scrollbar = self.verticalScrollBar()
        if not scrollbar.isVisible():
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        step_multiplier = 85  
        target_value = scrollbar.value() - (delta / 120) * step_multiplier
        target_value = max(scrollbar.minimum(), min(target_value, scrollbar.maximum()))

        if self._scroll_anim is None:
            self._scroll_anim = QPropertyAnimation(scrollbar, b"value")
            self._scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
            self._scroll_anim.setDuration(240)  

        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(scrollbar.value())
        self._scroll_anim.setEndValue(int(target_value))
        self._scroll_anim.start()
        event.accept()


class GraphicsPreviewView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setStyleSheet("background-color: #111111; border: 1px dashed #2E2E2E; border-radius: 6px;")
        
    def set_pixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap_item and not self.pixmap_item.pixmap().isNull():
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        
    def wheelEvent(self, event: QWheelEvent):
        if not self.pixmap_item.pixmap().isNull():
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)


class QueueDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        name = index.data(Qt.DisplayRole)
        status = index.data(QueueModel.StatusRole)
        progress = index.data(QueueModel.ProgressRole)
        thumbnail = index.data(QueueModel.ThumbnailRole)

        is_hovered = option.state & QStyle.State_MouseOver
        is_selected = option.state & QStyle.State_Selected

        rect = option.rect

        bg_color = QColor("#141416")
        border_color = QColor("#202024")
        if is_selected:
            bg_color = QColor("#1D1D21")
            border_color = QColor("#0A84FF")
        elif is_hovered:
            bg_color = QColor("#18181C")

        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)

        thumb_rect = rect.adjusted(10, 6, 10, 6)
        thumb_rect.setWidth(40)
        thumb_rect.setHeight(40)
        if thumbnail and not thumbnail.isNull():
            painter.drawPixmap(thumb_rect, thumbnail)
        else:
            painter.setBrush(QColor("#24242A"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(thumb_rect, 4, 4)
            painter.setPen(QColor("#7C7C82"))
            font = painter.font()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(thumb_rect, Qt.AlignCenter, "IMG")

        text_rect = rect.adjusted(60, 6, -110, -6)
        painter.setPen(QColor("#FFFFFF") if is_selected else QColor("#CCCCCC"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, name)

        if status == "processing":
            pb_rect = rect.adjusted(rect.width() - 170, 22, -40, -22)
            painter.setBrush(QColor("#18181C"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(pb_rect, 3, 3)

            chunk_width = int(pb_rect.width() * (progress / 100.0))
            if chunk_width > 0:
                active_rect = pb_rect
                active_rect.setWidth(chunk_width)
                painter.setBrush(QColor("#0A84FF"))
                painter.drawRoundedRect(active_rect, 3, 3)
        elif status == "success":
            status_rect = rect.adjusted(rect.width() - 160, 6, -40, -6)
            painter.setPen(QColor("#30D158"))
            painter.drawText(status_rect, Qt.AlignVCenter | Qt.AlignRight, "Done")
        elif status == "failed":
            status_rect = rect.adjusted(rect.width() - 160, 6, -40, -6)
            painter.setPen(QColor("#FF453A"))
            painter.drawText(status_rect, Qt.AlignVCenter | Qt.AlignRight, "Failed")

        delete_rect = rect.adjusted(rect.width() - 30, 16, -15, -16)
        if is_hovered:
            painter.setPen(QColor("#FF453A"))
        else:
            painter.setPen(QColor("#666666"))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(delete_rect, Qt.AlignCenter, "×")

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 52)