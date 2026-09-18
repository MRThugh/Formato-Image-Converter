import threading
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image, ProcessingResult
from utils.filenames import get_unique_output_path
from utils.logging import get_logger

logger = get_logger("ConversionWorker")


class BatchConversionWorker(QThread):
    # Signals emitted to the Main GUI Thread (Thread-Safe)
    file_started = Signal(str)                                         # filepath
    file_progress = Signal(str, int, str)                              # filepath, percent, status
    file_completed = Signal(str, bool, str, str, int, int, bool, int)  # filepath, success, error, out_path, size, target, achieved, quality
    overall_progress = Signal(int, int, int)                           # completed, total, percentage
    batch_finished = Signal(int, int, int, bool)                       # success_count, fail_count, cancel_count, cancelled

    def __init__(
        self,
        filepaths: List[str],
        settings: ConversionSettings,
        output_dir: Path,
        parent=None
    ):
        super().__init__(parent)
        self.filepaths = list(filepaths)
        self.settings = settings
        self.output_dir = Path(output_dir)
        self.cancel_event = threading.Event()
        self._is_cancelled = False

    def request_cancellation(self) -> None:
        """Signals the worker to cancel processing as soon as possible."""
        self._is_cancelled = True
        self.cancel_event.set()
        logger.info("Batch conversion cancellation requested by user.")

    def run(self) -> None:
        total = len(self.filepaths)
        if total == 0:
            self.batch_finished.emit(0, 0, 0, False)
            return

        logger.info(f"Starting batch conversion of {total} files to format {self.settings.fmt}...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        fail_count = 0
        cancel_count = 0

        reserved_paths: Set[Path] = set()

        for idx, fp in enumerate(self.filepaths):
            if self.cancel_event.is_set():
                # Remaining files are marked as cancelled
                for rem_fp in self.filepaths[idx:]:
                    cancel_count += 1
                    self.file_completed.emit(rem_fp, False, "Cancelled", "", 0, 0, False, 0)
                break

            in_path = Path(fp)
            self.file_started.emit(fp)
            self.file_progress.emit(fp, 15, "processing")

            # Resolve unique non-colliding destination path
            ext = self.settings.fmt.lower()
            if ext == "jpeg":
                ext = "jpg"

            out_path = get_unique_output_path(
                output_dir=self.output_dir,
                stem=in_path.stem,
                extension=ext,
                prefix=self.settings.pref,
                suffix=self.settings.suff,
                index_hint=idx + 1 if (self.settings.pref or self.settings.suff) else None,
                reserved_paths=reserved_paths
            )

            try:
                res: ProcessingResult = process_image(
                    source=in_path,
                    settings=self.settings,
                    output_path=out_path,
                    preview=False,
                    cancel_event=self.cancel_event
                )

                if res.was_cancelled or self.cancel_event.is_set():
                    cancel_count += 1
                    self.file_completed.emit(fp, False, "Cancelled", "", 0, 0, False, 0)
                    # Loop will break on next iteration
                elif res.success:
                    success_count += 1
                    self.file_progress.emit(fp, 100, "completed")
                    self.file_completed.emit(
                        fp,
                        True,
                        "",
                        str(res.output_path),
                        res.actual_size_bytes,
                        res.target_size_bytes,
                        res.target_size_achieved,
                        res.final_quality
                    )
                    logger.info(f"Converted: {in_path.name} -> {out_path.name} ({res.actual_size_bytes} bytes)")
                else:
                    fail_count += 1
                    self.file_progress.emit(fp, 100, "failed")
                    self.file_completed.emit(
                        fp,
                        False,
                        res.error_msg,
                        "",
                        0,
                        0,
                        False,
                        0
                    )
                    logger.warning(f"Failed converting {in_path.name}: {res.error_msg}")

            except Exception as e:
                fail_count += 1
                logger.error(f"Unexpected error converting {in_path.name}: {e}", exc_info=True)
                self.file_completed.emit(fp, False, str(e), "", 0, 0, False, 0)

            # Overall progress calculation
            completed = success_count + fail_count + cancel_count
            pct = int((completed / float(total)) * 100)
            self.overall_progress.emit(completed, total, pct)

        logger.info(f"Batch conversion finished. Success: {success_count}, Failed: {fail_count}, Cancelled: {cancel_count}")
        self.batch_finished.emit(success_count, fail_count, cancel_count, self._is_cancelled)
