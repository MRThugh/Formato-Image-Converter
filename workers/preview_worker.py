import threading
from pathlib import Path
from typing import Optional, Union
from PIL import Image
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image, ProcessingResult


class PreviewWorker(QThread):
    preview_ready = Signal(QImage, int)  # qimage, request_id
    preview_failed = Signal(str, int)    # error_msg, request_id

    def __init__(
        self,
        source_path: Union[str, Path],
        settings: ConversionSettings,
        request_id: int,
        cached_source_img: Optional[Image.Image] = None,
        parent=None
    ):
        super().__init__(parent)
        self.source_path = str(source_path)
        self.settings = settings
        self.request_id = request_id
        self.cached_source_img = cached_source_img
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        if self.cancel_event.is_set():
            return

        try:
            # If a cached thumbnail PIL image exists for this file, use it to save disk/decode time
            src = self.cached_source_img if self.cached_source_img is not None else self.source_path

            res: ProcessingResult = process_image(
                source=src,
                settings=self.settings,
                output_path=None,
                preview=True,
                preview_max_dim=800,
                cancel_event=self.cancel_event
            )

            if self.cancel_event.is_set() or res.was_cancelled or not res.success:
                return

            if res.preview_image is None:
                return

            # Convert PIL image to QImage
            pil_rgba = res.preview_image.convert("RGBA")
            data = pil_rgba.tobytes("raw", "RGBA")
            w, h = pil_rgba.size

            qimg = QImage(data, w, h, QImage.Format_RGBA8888).copy()

            if not self.cancel_event.is_set():
                self.preview_ready.emit(qimg, self.request_id)

        except Exception as e:
            if not self.cancel_event.is_set():
                self.preview_failed.emit(str(e), self.request_id)
