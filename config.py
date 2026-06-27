import os

# ==================== CONFIGURATION ====================
LOGO_IMAGE_PATH = os.path.join("assets", "logo.png")
WINDOW_ICON_PATH = os.path.join("assets", "icon.ico")
# ======================================================

# Style Sheet representing the dark professional workspace
QSS_STYLE = """
QMainWindow {
    background-color: #0B0B0C;
}
QWidget {
    color: #E2E2E6;
    font-family: "Segoe UI", -apple-system, Arial, sans-serif;
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
    padding: 6px 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #24242A;
    border-color: #383842;
}
QPushButton:pressed {
    background-color: #0A84FF;
    border-color: #0A84FF;
    color: #FFFFFF;
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
QFrame#Card {
    background-color: #131315;
    border: 1px solid #202024;
    border-radius: 8px;
}
QLineEdit {
    background-color: #18181C;
    border: 1px solid #26262B;
    border-radius: 5px;
    padding: 5px;
    color: #FFFFFF;
}
QLineEdit:focus {
    border: 1px solid #0A84FF;
}
QComboBox {
    background-color: #18181C;
    border: 1px solid #26262B;
    border-radius: 5px;
    padding: 4px;
    color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
}
QCheckBox {
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
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
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #359AFF;
}
QProgressBar {
    background-color: #18181C;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #0A84FF;
    border-radius: 4px;
}
QListView {
    background-color: transparent;
    border: none;
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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""