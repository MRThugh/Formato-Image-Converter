import threading
from pathlib import Path
from typing import List, Union
from PySide6.QtCore import QThread, Signal
from core.pdf_builder import build_pdf_from_images


class PdfWorker(QThread):
    finished = Signal(bool, str)  # success, message

    def __init__(
        self,
        image_paths: List[Union[str, Path]],
        output_pdf_path: Union[str, Path],
        page_size_name: str = "A4",
        orientation: str = "Portrait",
        fit_mode: str = "Fit",
        margin: int = 20,
        parent=None
    ):
        super().__init__(parent)
        self.image_paths = image_paths
        self.output_pdf_path = output_pdf_path
        self.page_size_name = page_size_name
        self.orientation = orientation
        self.fit_mode = fit_mode
        self.margin = margin
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        success, msg = build_pdf_from_images(
            image_paths=self.image_paths,
            output_pdf_path=self.output_pdf_path,
            page_size_name=self.page_size_name,
            orientation=self.orientation,
            fit_mode=self.fit_mode,
            margin=self.margin,
            cancel_event=self.cancel_event
        )
        self.finished.emit(success, msg)
