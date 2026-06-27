import sys
from PySide6.QtWidgets import QApplication
from views.main_window import FormatoApp


def main():
    app = QApplication(sys.argv)
    window = FormatoApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()