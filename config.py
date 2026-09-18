import os
from pathlib import Path
from utils.paths import get_asset_path

# ==================== APPLICATION IDENTITY ====================
APP_NAME = "Formato"
APP_VERSION = "2.6.0"
APP_AUTHOR = "Ali Kamrani"
APP_DESCRIPTION = "Professional Native Image Studio & Batch Conversion Tool"
APP_GITHUB = "https://github.com/MRThugh/Formato-Image-Converter"

# ==================== ASSET PATHS ====================
LOGO_IMAGE_PATH = str(get_asset_path("logo.png"))
WINDOW_ICON_PATH = str(get_asset_path("icon.ico"))

# ==================== SUPPORTED FORMATS ====================
SUPPORTED_FORMATS = ("JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF")
RESIZE_MODES = ("Fit (Maintain AR)", "Fill/Crop", "Stretch")
WATERMARK_POSITIONS = ("Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center")

# ==================== THEME & STYLESHEET ====================
QSS_STYLE = """
QMainWindow {
    background-color: #0B0B0C;
}
QWidget {
    color: #E2E2E6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    font-size: 12px;
}
QFrame#Sidebar {
    background-color: #121214;
    border-right: 1px solid #1E1E22;
}
QPushButton {
    background-color: #1A1A1E;
    border: 1px solid #28282E;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
    color: #E2E2E6;
}
QPushButton:hover {
    background-color: #24242A;
    border-color: #383842;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #0A84FF;
    border-color: #0A84FF;
    color: #FFFFFF;
}
QPushButton:disabled {
    background-color: #141416;
    border-color: #1E1E22;
    color: #55555A;
}
QPushButton#PrimaryBtn {
    background-color: #0A84FF;
    border: 1px solid #0A84FF;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0070E0;
    border-color: #0070E0;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #16365C;
    border-color: #16365C;
    color: #6C8CAE;
}
QPushButton#CancelBtn {
    background-color: #321919;
    border: 1px solid #5A2323;
    color: #FF6961;
    font-weight: 600;
}
QPushButton#CancelBtn:hover {
    background-color: #481E1E;
    border-color: #FF453A;
    color: #FFFFFF;
}
QPushButton#CancelBtn:disabled {
    background-color: #1F1414;
    border-color: #2A1A1A;
    color: #6A4444;
}
QPushButton#SidebarBtn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 8px 12px;
    font-size: 13px;
    color: #9A9A9F;
}
QPushButton#SidebarBtn:hover {
    background-color: #1C1C21;
    color: #FFFFFF;
}
QPushButton#SidebarBtn:checked {
    background-color: #1C1C21;
    color: #0A84FF;
    font-weight: 600;
}
QFrame#Card {
    background-color: #131315;
    border: 1px solid #202024;
    border-radius: 8px;
}
QLineEdit {
    background-color: #18181C;
    border: 1px solid #26262B;
    border-radius: 5px;
    padding: 6px 8px;
    color: #FFFFFF;
}
QLineEdit:focus {
    border: 1px solid #0A84FF;
}
QComboBox {
    background-color: #18181C;
    border: 1px solid #26262B;
    border-radius: 5px;
    padding: 5px 8px;
    color: #FFFFFF;
}
QComboBox:focus {
    border: 1px solid #0A84FF;
}
QComboBox QAbstractItemView {
    background-color: #18181C;
    border: 1px solid #26262B;
    selection-background-color: #0A84FF;
    selection-color: #FFFFFF;
    color: #E2E2E6;
}
QCheckBox {
    spacing: 6px;
    color: #CCCCCC;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    background-color: #18181C;
    border: 1px solid #26262B;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background-color: #0A84FF;
    border-color: #0A84FF;
}
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #202024;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #0A84FF;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #359AFF;
}
QProgressBar {
    background-color: #18181C;
    border: 1px solid #202024;
    border-radius: 4px;
    text-align: center;
    color: #FFFFFF;
    font-weight: 500;
}
QProgressBar::chunk {
    background-color: #0A84FF;
    border-radius: 3px;
}
QListView {
    background-color: transparent;
    border: none;
    outline: none;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #0B0B0C;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #202024;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #2E2E36;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
