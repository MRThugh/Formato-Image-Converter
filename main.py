import sys
import traceback
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from config import APP_NAME, APP_VERSION, APP_AUTHOR, WINDOW_ICON_PATH
from views.main_window import MainWindow
from utils.logging import get_logger

logger = get_logger("Main")


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled desktop exception:\n{err_str}")


def main():
    sys.excepthook = handle_uncaught_exception

    # High-DPI Scaling attributes
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_AUTHOR)

    icon_path = Path(WINDOW_ICON_PATH)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    logger.info(f"{APP_NAME} desktop application started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
