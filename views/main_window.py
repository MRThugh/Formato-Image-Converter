import os
import time
import threading
import concurrent.futures
from pathlib import Path

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QEasingCurve, QPropertyAnimation, QModelIndex
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QComboBox, QSlider, QCheckBox, QLineEdit,
    QFileDialog, QMessageBox, QProgressBar, QGridLayout, QListView, QGraphicsPixmapItem
)
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QCursor, QImage, QPixmap

from config import QSS_STYLE, WINDOW_ICON_PATH
from utils import parse_int, get_resize_dimensions
from core.image_processor import convert_image, apply_watermark
from models.queue_model import QueueModel
from views.widgets import ClickableLabel, SmoothScrollArea, GraphicsPreviewView, QueueDelegate


class FormatoApp(QMainWindow):
    preview_ready = Signal(QImage)
    thumbnail_loaded = Signal(int, QImage)
    progress_updated = Signal(str, float)
    batch_finished = Signal()
    preview_cache_ready = Signal()

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Formato - Professional Studio")
        self.resize(1400, 950)
        self.setMinimumSize(1150, 750)
        
        if os.path.exists(WINDOW_ICON_PATH):
            self.setWindowIcon(QIcon(WINDOW_ICON_PATH))

        self.selected_files = []
        self.preview_thread = None
        self.preview_pending = False
        self.current_preview_file = None
        self.last_preview_time = 0
        self.favicon_source = None

        self._cached_preview_image = None
        self._cached_preview_path = None

        self.queue_model = QueueModel()
        self.thumbnail_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)

        self.setAcceptDrops(True)
        self.setup_ui()
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._process_preview)

        self.preview_ready.connect(self._handle_preview_ready)
        self.thumbnail_loaded.connect(self._handle_thumbnail_loaded)
        self.progress_updated.connect(self._update_file_progress)
        self.batch_finished.connect(self.finish_conversion)
        self.preview_cache_ready.connect(self.trigger_preview_update)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp', '.gif'}
        new_files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if Path(file_path).suffix.lower() in valid_exts and file_path not in self.selected_files:
                new_files.append(file_path)
        
        if new_files:
            current_count = len(self.selected_files)
            for idx, filepath in enumerate(new_files):
                if self.queue_model.add_file(filepath):
                    self.selected_files.append(filepath)
                    self._async_load_thumb(filepath, current_count + idx)
            
            self.update_queue_selection()

    def setup_ui(self):
        self.setStyleSheet(QSS_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar Layout ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 20)
        sidebar_layout.setSpacing(10)

        logo_label = QLabel("Formato")
        logo_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; padding-left: 20px;")
        sidebar_layout.addWidget(logo_label)

        self.active_indicator = QFrame(self.sidebar)
        self.active_indicator.setStyleSheet("background-color: #0A84FF; border-radius: 2px;")
        self.active_indicator.resize(4, 40)
        self.active_indicator.move(0, 80)

        self.sidebar_button_positions = {}

        self.btn_batch = QPushButton("⚡ Batch Process")
        self.btn_batch.setObjectName("SidebarBtn")
        self.btn_batch.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        self.btn_batch.setFixedHeight(40)
        self.btn_batch.clicked.connect(lambda: self.select_frame("batch"))
        sidebar_layout.addWidget(self.btn_batch)
        self.sidebar_button_positions["batch"] = 80

        self.btn_pdf = QPushButton("📄 PDF Export")
        self.btn_pdf.setObjectName("SidebarBtn")
        self.btn_pdf.setFixedHeight(40)
        self.btn_pdf.clicked.connect(lambda: self.select_frame("pdf"))
        sidebar_layout.addWidget(self.btn_pdf)
        self.sidebar_button_positions["pdf"] = 130

        self.btn_icon = QPushButton("🎨 Icon Generator")
        self.btn_icon.setObjectName("SidebarBtn")
        self.btn_icon.setFixedHeight(40)
        self.btn_icon.clicked.connect(lambda: self.select_frame("icon"))
        sidebar_layout.addWidget(self.btn_icon)
        self.sidebar_button_positions["icon"] = 180

        sidebar_layout.addStretch()

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.status_label)

        main_layout.addWidget(self.sidebar)

        # --- Dynamic View Container ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.batch_view = QWidget()
        self.pdf_view = QWidget()
        self.icon_view = QWidget()

        self.stacked_widget.addWidget(self.batch_view)
        self.stacked_widget.addWidget(self.pdf_view)
        self.stacked_widget.addWidget(self.icon_view)

        self.setup_batch_view()
        self.setup_pdf_view()
        self.setup_icon_view()

    def select_frame(self, frame_name):
        self.btn_batch.setStyleSheet("color: #A0A0A0;")
        self.btn_pdf.setStyleSheet("color: #A0A0A0;")
        self.btn_icon.setStyleSheet("color: #A0A0A0;")

        target_y = self.sidebar_button_positions.get(frame_name, 80)
        
        self.anim = QPropertyAnimation(self.active_indicator, b"pos")
        self.anim.setDuration(280)
        self.anim.setStartValue(QPoint(0, self.active_indicator.y()))
        self.anim.setEndValue(QPoint(0, target_y))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        if frame_name == "batch":
            self.btn_batch.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            self.stacked_widget.setCurrentWidget(self.batch_view)
        elif frame_name == "pdf":
            self.btn_pdf.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            self.stacked_widget.setCurrentWidget(self.pdf_view)
        elif frame_name == "icon":
            self.btn_icon.setStyleSheet("color: #FFFFFF; font-weight: bold;")
            self.stacked_widget.setCurrentWidget(self.icon_view)

    def create_card(self, parent_layout, title):
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #E2E2E6;")
        card_layout.addWidget(title_lbl)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        card_layout.addWidget(content_widget)

        parent_layout.addWidget(card)
        return content_layout

    def setup_batch_view(self):
        layout = QHBoxLayout(self.batch_view)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        queue_card = QFrame()
        queue_card.setObjectName("Card")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(15, 15, 15, 15)
        
        q_title = QLabel("Queue (Drag & Drop Supported)")
        q_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        queue_layout.addWidget(q_title)

        self.queue_view = QListView()
        self.queue_view.setModel(self.queue_model)
        self.queue_view.setItemDelegate(QueueDelegate(self))
        self.queue_view.clicked.connect(self.handle_queue_click)
        queue_layout.addWidget(self.queue_view)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Files")
        self.btn_add.clicked.connect(self.add_files)
        self.btn_clear = QPushButton("🗑 Clear")
        self.btn_clear.setStyleSheet("background-color: #5C3A3A; border-color: #7A4C4C;")
        self.btn_clear.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        queue_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        queue_layout.addWidget(self.progress_bar)

        left_layout.addWidget(queue_card, stretch=6)

        preview_card = QFrame()
        preview_card.setObjectName("Card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(15, 15, 15, 15)

        p_title = QLabel("Live Preview (Drag to Pan / Scroll to Zoom)")
        p_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        preview_layout.addWidget(p_title)

        self.preview_canvas = GraphicsPreviewView()
        preview_layout.addWidget(self.preview_canvas, stretch=1)

        left_layout.addWidget(preview_card, stretch=5)
        layout.addWidget(left_panel, stretch=6)

        self.right_scroll = SmoothScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setMinimumWidth(420)
        self.right_scroll.setMaximumWidth(420)
        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 10, 0)
        right_layout.setSpacing(12)

        top_bar_layout = QHBoxLayout()
        panel_title = QLabel("Workspace Settings")
        panel_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        
        self.btn_reset_all = QPushButton("🔄 Reset Settings")
        self.btn_reset_all.setStyleSheet("""
            QPushButton {
                background-color: #1F1F24;
                border: 1px solid #2C2C35;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #2C2C35;
            }
        """)
        self.btn_reset_all.clicked.connect(self.reset_all_settings)
        
        top_bar_layout.addWidget(panel_title)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.btn_reset_all)
        right_layout.addLayout(top_bar_layout)

        card_out = self.create_card(right_layout, "Output Format")
        self.out_format_combo = QComboBox()
        self.out_format_combo.addItems(["JPEG", "PNG", "WEBP", "TIFF", "BMP", "GIF"])
        card_out.addWidget(self.out_format_combo)

        qual_lbl_layout = QHBoxLayout()
        qual_lbl_layout.addWidget(QLabel("Quality"))
        card_out.addLayout(qual_lbl_layout)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        card_out.addWidget(self.quality_slider)

        smart_lay = QHBoxLayout()
        self.chk_smart = QCheckBox("Smart Compression")
        self.smart_kb_entry = QLineEdit("500")
        self.smart_kb_entry.setFixedWidth(60)
        smart_lay.addWidget(self.chk_smart)
        smart_lay.addStretch()
        smart_lay.addWidget(QLabel("Target KB:"))
        smart_lay.addWidget(self.smart_kb_entry)
        card_out.addLayout(smart_lay)

        card_res = self.create_card(right_layout, "Smart Resize (Leave one empty to keep aspect ratio)")
        res_row = QHBoxLayout()
        self.entry_width = QLineEdit()
        self.entry_width.setPlaceholderText("Width")
        self.entry_width.setFixedWidth(70)
        self.entry_width.textChanged.connect(self.trigger_preview_update)

        self.entry_height = QLineEdit()
        self.entry_height.setPlaceholderText("Height")
        self.entry_height.setFixedWidth(70)
        self.entry_height.textChanged.connect(self.trigger_preview_update)

        self.resize_mode_combo = QComboBox()
        self.resize_mode_combo.addItems(["Stretch", "Fit (Maintain AR)", "Fill/Crop"])
        self.resize_mode_combo.currentTextChanged.connect(self.trigger_preview_update)

        res_row.addWidget(self.entry_width)
        res_row.addWidget(QLabel("×"))
        res_row.addWidget(self.entry_height)
        res_row.addSpacing(10)
        res_row.addWidget(self.resize_mode_combo, stretch=1)
        card_res.addLayout(res_row)

        card_adj = self.create_card(right_layout, "Advanced Adjustments (Double-click label to reset)")
        self.adj_brightness = self._add_slider_row(card_adj, "Brightness", 2, 30, 10)
        self.adj_contrast = self._add_slider_row(card_adj, "Contrast", 2, 30, 10)
        self.adj_saturation = self._add_slider_row(card_adj, "Saturation", 2, 30, 10)
        self.adj_sharpness = self._add_slider_row(card_adj, "Sharpness", 2, 50, 10)

        card_enh = self.create_card(right_layout, "Enhancements & Filters")
        filters_layout = QGridLayout()
        self.chk_gray = QCheckBox("Grayscale")
        self.chk_auto = QCheckBox("Auto-Contrast")
        self.chk_sharp = QCheckBox("Sharpen")
        self.chk_blur = QCheckBox("Blur")
        self.chk_contour = QCheckBox("Contour")
        self.chk_emboss = QCheckBox("Emboss")
        self.chk_edge = QCheckBox("Edge Enhance")

        self.chk_gray.stateChanged.connect(self.trigger_preview_update)
        self.chk_auto.stateChanged.connect(self.trigger_preview_update)
        self.chk_sharp.stateChanged.connect(self.trigger_preview_update)
        self.chk_blur.stateChanged.connect(self.trigger_preview_update)
        self.chk_contour.stateChanged.connect(self.trigger_preview_update)
        self.chk_emboss.stateChanged.connect(self.trigger_preview_update)
        self.chk_edge.stateChanged.connect(self.trigger_preview_update)

        filters_layout.addWidget(self.chk_gray, 0, 0)
        filters_layout.addWidget(self.chk_auto, 0, 1)
        filters_layout.addWidget(self.chk_sharp, 0, 2)
        filters_layout.addWidget(self.chk_blur, 1, 0)
        filters_layout.addWidget(self.chk_contour, 1, 1)
        filters_layout.addWidget(self.chk_emboss, 1, 2)
        filters_layout.addWidget(self.chk_edge, 2, 0, 1, 3)
        card_enh.addLayout(filters_layout)

        card_meta = self.create_card(right_layout, "Metadata Manager")
        self.chk_preserve_exif = QCheckBox("Preserve Original EXIF")
        self.chk_preserve_exif.setChecked(True)
        self.chk_meta_enable = QCheckBox("Write Custom Metadata")
        
        self.meta_author = QLineEdit()
        self.meta_author.setPlaceholderText("Author Name")
        self.meta_copyright = QLineEdit()
        self.meta_copyright.setPlaceholderText("Copyright Info")
        self.meta_desc = QLineEdit()
        self.meta_desc.setPlaceholderText("Image Description / Caption")

        card_meta.addWidget(self.chk_preserve_exif)
        card_meta.addWidget(self.chk_meta_enable)
        card_meta.addWidget(self.meta_author)
        card_meta.addWidget(self.meta_copyright)
        card_meta.addWidget(self.meta_desc)

        card_wm = self.create_card(right_layout, "Watermark & Renaming")
        wm_path_row = QHBoxLayout()
        self.entry_wm_path = QLineEdit()
        self.entry_wm_path.setReadOnly(True)
        self.entry_wm_path.setPlaceholderText("Watermark (PNG)")
        self.btn_select_wm = QPushButton("📁")
        self.btn_select_wm.setFixedWidth(40)
        self.btn_select_wm.clicked.connect(self.select_watermark)
        wm_path_row.addWidget(self.entry_wm_path)
        wm_path_row.addWidget(self.btn_select_wm)
        card_wm.addLayout(wm_path_row)

        wm_adv1 = QHBoxLayout()
        wm_adv1.addWidget(QLabel("Pos:"))
        self.wm_pos_combo = QComboBox()
        self.wm_pos_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"])
        self.wm_pos_combo.setCurrentText("Bottom Right")
        self.wm_pos_combo.currentTextChanged.connect(self.trigger_preview_update)
        wm_adv1.addWidget(self.wm_pos_combo)
        wm_adv1.addWidget(QLabel("Size:"))
        self.wm_size_slider = QSlider(Qt.Horizontal)
        self.wm_size_slider.setRange(5, 50)
        self.wm_size_slider.setValue(15)
        self.wm_size_slider.valueChanged.connect(self.trigger_preview_update)
        wm_adv1.addWidget(self.wm_size_slider)
        card_wm.addLayout(wm_adv1)

        wm_adv2 = QHBoxLayout()
        wm_adv2.addWidget(QLabel("Opacity:"))
        self.wm_opacity_slider = QSlider(Qt.Horizontal)
        self.wm_opacity_slider.setRange(0, 100)
        self.wm_opacity_slider.setValue(100)
        self.wm_opacity_slider.valueChanged.connect(self.trigger_preview_update)
        wm_adv2.addWidget(self.wm_opacity_slider)
        wm_adv2.addWidget(QLabel("Margin:"))
        self.wm_mx = QLineEdit("10")
        self.wm_mx.setFixedWidth(40)
        self.wm_mx.textChanged.connect(self.trigger_preview_update)
        self.wm_my = QLineEdit("10")
        self.wm_my.setFixedWidth(40)
        self.wm_my.textChanged.connect(self.trigger_preview_update)
        wm_adv2.addWidget(self.wm_mx)
        wm_adv2.addWidget(self.wm_my)
        card_wm.addLayout(wm_adv2)

        rename_row = QHBoxLayout()
        self.rename_prefix = QLineEdit()
        self.rename_prefix.setPlaceholderText("Prefix")
        self.rename_suffix = QLineEdit()
        self.rename_suffix.setPlaceholderText("Suffix")
        rename_row.addWidget(self.rename_prefix)
        rename_row.addWidget(self.rename_suffix)
        card_wm.addLayout(rename_row)

        card_dest = self.create_card(right_layout, "Destination Folder")
        dest_row = QHBoxLayout()
        self.output_folder_entry = QLineEdit()
        self.output_folder_entry.setPlaceholderText("Required")
        self.output_folder_entry.setReadOnly(True)
        self.btn_select_dest = QPushButton("📁")
        self.btn_select_dest.setFixedWidth(40)
        self.btn_select_dest.clicked.connect(self.choose_output_folder)
        dest_row.addWidget(self.output_folder_entry)
        dest_row.addWidget(self.btn_select_dest)
        card_dest.addLayout(dest_row)

        self.convert_btn = QPushButton("🚀 START PROCESSING")
        self.convert_btn.setFixedHeight(45)
        self.convert_btn.setStyleSheet("background-color: #0A84FF; color: #FFFFFF; font-weight: bold; font-size: 14px;")
        self.convert_btn.clicked.connect(self.start_conversion)
        card_dest.addWidget(self.convert_btn)

        preset_row = QHBoxLayout()
        self.btn_save_preset = QPushButton("💾 Save Preset")
        self.btn_save_preset.clicked.connect(self.save_preset)
        self.btn_load_preset = QPushButton("📂 Load Preset")
        self.btn_load_preset.clicked.connect(self.load_preset)
        preset_row.addWidget(self.btn_save_preset)
        preset_row.addWidget(self.btn_load_preset)
        right_layout.addLayout(preset_row)

        right_layout.addStretch()
        self.right_scroll.setWidget(right_container)

        self.right_panel_widget = QWidget()
        right_panel_layout = QHBoxLayout(self.right_panel_widget)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(0)

        self.toggle_container = QWidget()
        self.toggle_container.setFixedWidth(20)
        toggle_v_layout = QVBoxLayout(self.toggle_container)
        toggle_v_layout.setContentsMargins(0, 0, 0, 0)
        toggle_v_layout.setAlignment(Qt.AlignCenter)

        self.btn_toggle_panel = QPushButton("▶")
        self.btn_toggle_panel.setFixedWidth(14)
        self.btn_toggle_panel.setFixedHeight(80)
        self.btn_toggle_panel.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_panel.setStyleSheet("""
            QPushButton {
                background-color: #121214;
                border: 1px solid #202024;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                color: #A0A0A0;
                padding: 0px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1A1A1E;
                color: #FFFFFF;
            }
        """)
        self.btn_toggle_panel.clicked.connect(self.toggle_right_panel)
        toggle_v_layout.addWidget(self.btn_toggle_panel)

        right_panel_layout.addWidget(self.toggle_container)
        right_panel_layout.addWidget(self.right_scroll)

        layout.addWidget(self.right_panel_widget)

    def _add_slider_row(self, layout, name, min_val, max_val, default_val):
        row = QHBoxLayout()
        
        lbl_name = ClickableLabel(name)
        lbl_name.setFixedWidth(80)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(self.trigger_preview_update)
        
        lbl_val = ClickableLabel(f"{default_val/10.0:.1f}")
        lbl_val.setFixedWidth(30)
        lbl_val.setAlignment(Qt.AlignRight)

        def reset():
            slider.setValue(10)
            self.trigger_preview_update()

        lbl_name.double_clicked.connect(reset)
        lbl_val.double_clicked.connect(reset)
        slider.valueChanged.connect(lambda v: lbl_val.setText(f"{v/10.0:.1f}"))

        row.addWidget(lbl_name)
        row.addWidget(slider)
        row.addWidget(lbl_val)
        layout.addLayout(row)
        return slider

    def setup_pdf_view(self):
        layout = QVBoxLayout(self.pdf_view)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)

        container = QFrame()
        container.setObjectName("Card")
        container.setFixedSize(600, 400)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(20)
        c_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("📄 PDF Builder")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(title)

        desc = QLabel("Combine all files in your 'Queue' into a single PDF document.")
        desc.setStyleSheet("color: #888888; font-size: 14px;")
        desc.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(desc)

        self.btn_export_pdf = QPushButton("Export to PDF")
        self.btn_export_pdf.setFixedHeight(50)
        self.btn_export_pdf.setFixedWidth(200)
        self.btn_export_pdf.setStyleSheet("background-color: #0A84FF; color: #FFFFFF; font-weight: bold; font-size: 15px;")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        c_layout.addWidget(self.btn_export_pdf)

        layout.addWidget(container)

    def setup_icon_view(self):
        layout = QVBoxLayout(self.icon_view)
        layout.setContentsMargins(30, 30, 30, 30)

        container = QFrame()
        container.setObjectName("Card")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(40, 40, 40, 40)
        c_layout.setSpacing(15)

        title = QLabel("🎨 Icon & Favicon Generator")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(title)

        src_row = QHBoxLayout()
        self.favicon_src_entry = QLineEdit()
        self.favicon_src_entry.setReadOnly(True)
        self.favicon_src_entry.setPlaceholderText("No image selected")
        self.btn_select_fav = QPushButton("📁 Select Source")
        self.btn_select_fav.clicked.connect(self.select_favicon_source)
        src_row.addWidget(self.favicon_src_entry)
        src_row.addWidget(self.btn_select_fav)
        c_layout.addLayout(src_row)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Target Type:"))
        self.icon_type_combo = QComboBox()
        self.icon_type_combo.addItems(["Favicon (Web)", "Icon (App)"])
        self.icon_type_combo.currentTextChanged.connect(self.update_default_sizes)
        type_row.addWidget(self.icon_type_combo)
        type_row.addStretch()
        c_layout.addLayout(type_row)

        self.sizes_box = QFrame()
        self.sizes_box.setStyleSheet("background-color: #121212; border: 1px solid #2B2B2B; border-radius: 8px;")
        grid_lay = QGridLayout(self.sizes_box)
        grid_lay.setContentsMargins(15, 15, 15, 15)
        grid_lay.setSpacing(10)

        self.size_checkboxes = {}
        sizes = [
            (16, 16), (32, 32), (48, 48),
            (64, 64), (128, 128), (180, 180),
            (192, 192), (256, 256), (512, 512)
        ]
        
        row, col = 0, 0
        for sz in sizes:
            chk = QCheckBox(f"{sz[0]}×{sz[1]}")
            grid_lay.addWidget(chk, row, col)
            self.size_checkboxes[sz] = chk
            col += 1
            if col > 2:
                col = 0
                row += 1

        c_layout.addWidget(self.sizes_box)

        self.btn_generate_icons = QPushButton("⚡ Generate Icons")
        self.btn_generate_icons.setFixedHeight(50)
        self.btn_generate_icons.setStyleSheet("background-color: #0A84FF; color: #FFFFFF; font-weight: bold; font-size: 15px;")
        self.btn_generate_icons.clicked.connect(self.generate_icon)
        c_layout.addWidget(self.btn_generate_icons)

        layout.addWidget(container)
        self.update_default_sizes("Favicon (Web)")

    def update_default_sizes(self, choice):
        defaults = {
            "Favicon (Web)": [(16,16), (32,32), (180,180), (192,192), (256,256), (512,512)],
            "Icon (App)": [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256), (512,512)]
        }
        selected = defaults.get(choice, [(16,16), (32,32)])
        for size, chk in self.size_checkboxes.items():
            chk.setChecked(size in selected)

    def handle_queue_click(self, index: QModelIndex):
        rect = self.queue_view.visualRect(index)
        click_pos = self.queue_view.viewport().mapFromGlobal(QCursor.pos())

        if click_pos.x() > (rect.x() + rect.width() - 40):
            self.remove_file_by_row(index.row())
        else:
            filepath = self.queue_model.data(index, QueueModel.FilepathRole)
            self.set_preview_image(filepath)

    def remove_file_by_row(self, row):
        if 0 <= row < len(self.selected_files):
            filepath = self.selected_files[row]
            self.selected_files.pop(row)
            self.queue_model.remove_file(row)

            if self.current_preview_file == filepath:
                self.current_preview_file = None
                self._cached_preview_image = None
                self._cached_preview_path = None
                self.preview_canvas.scene.clear()
                self.preview_canvas.pixmap_item = QGraphicsPixmapItem()
                self.preview_canvas.scene.addItem(self.preview_canvas.pixmap_item)

            for r in range(row, len(self.selected_files)):
                self._async_load_thumb(self.selected_files[r], r)

            self.update_queue_selection()

    def toggle_right_panel(self):
        is_visible = self.right_scroll.maximumWidth() > 0
        
        start_val = 420 if is_visible else 0
        end_val = 0 if is_visible else 420
        
        self.panel_anim = QPropertyAnimation(self.right_scroll, b"maximumWidth")
        self.panel_anim.setDuration(250)
        self.panel_anim.setStartValue(start_val)
        self.panel_anim.setEndValue(end_val)
        self.panel_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        if is_visible:
            self.right_scroll.setMinimumWidth(0)
            self.btn_toggle_panel.setText("◀")
        else:
            self.btn_toggle_panel.setText("▶")
            self.right_scroll.setMinimumWidth(0)
            self.panel_anim.finished.connect(self._on_expand_finished)
            
        self.panel_anim.start()

    def _on_expand_finished(self):
        if self.right_scroll.maximumWidth() >= 420:
            self.right_scroll.setMinimumWidth(420)

    def reset_all_settings(self):
        self.out_format_combo.setCurrentText("JPEG")
        self.quality_slider.setValue(85)
        self.chk_smart.setChecked(False)
        self.smart_kb_entry.setText("500")
        
        self.entry_width.clear()
        self.entry_height.clear()
        self.resize_mode_combo.setCurrentText("Stretch")
        
        self.adj_brightness.setValue(10)
        self.adj_contrast.setValue(10)
        self.adj_saturation.setValue(10)
        self.adj_sharpness.setValue(10)
        
        self.chk_gray.setChecked(False)
        self.chk_auto.setChecked(False)
        self.chk_sharp.setChecked(False)
        self.chk_blur.setChecked(False)
        self.chk_contour.setChecked(False)
        self.chk_emboss.setChecked(False)
        self.chk_edge.setChecked(False)
        
        self.chk_preserve_exif.setChecked(True)
        self.chk_meta_enable.setChecked(False)
        self.meta_author.clear()
        self.meta_copyright.clear()
        self.meta_desc.clear()
        
        self.entry_wm_path.clear()
        self.wm_pos_combo.setCurrentText("Bottom Right")
        self.wm_size_slider.setValue(15)
        self.wm_opacity_slider.setValue(100)
        self.wm_mx.setText("10")
        self.wm_my.setText("10")
        self.rename_prefix.clear()
        self.rename_suffix.clear()
        
        self.trigger_preview_update()

    def save_preset(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Preset", "", "JSON Files (*.json)")
        if not file: return
        
        data = {
            "output_format": self.out_format_combo.currentText(),
            "quality": self.quality_slider.value(),
            "smart_compress": self.chk_smart.isChecked(),
            "target_kb": self.smart_kb_entry.text(),
            "resize_width": self.entry_width.text(),
            "resize_height": self.entry_height.text(),
            "resize_mode": self.resize_mode_combo.currentText(),
            "filter_gray": self.chk_gray.isChecked(),
            "filter_auto": self.chk_auto.isChecked(),
            "filter_sharp": self.chk_sharp.isChecked(),
            "filter_blur": self.chk_blur.isChecked(),
            "filter_contour": self.chk_contour.isChecked(),
            "filter_emboss": self.chk_emboss.isChecked(),
            "filter_edge": self.chk_edge.isChecked(),
            "preserve_exif": self.chk_preserve_exif.isChecked(),
            "meta_enable": self.chk_meta_enable.isChecked(),
            "meta_author": self.meta_author.text(),
            "meta_copyright": self.meta_copyright.text(),
            "meta_description": self.meta_desc.text(),
            "adj_brightness": self.adj_brightness.value(),
            "adj_contrast": self.adj_contrast.value(),
            "adj_saturation": self.adj_saturation.value(),
            "adj_sharpness": self.adj_sharpness.value(),
            "wm_pos": self.wm_pos_combo.currentText(),
            "wm_size": self.wm_size_slider.value(),
            "wm_opacity": self.wm_opacity_slider.value(),
            "wm_margin_x": self.wm_mx.text(),
            "wm_margin_y": self.wm_my.text()
        }
        try:
            with open(file, 'w') as f:
                import json
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Success", "Preset saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {e}")

    def load_preset(self):
        file, _ = QFileDialog.getOpenFileName(self, "Load Preset", "", "JSON Files (*.json)")
        if not file: return
        
        try:
            with open(file, 'r') as f:
                import json
                data = json.load(f)
            self.out_format_combo.setCurrentText(data.get("output_format", "JPEG"))
            self.quality_slider.setValue(data.get("quality", 85))
            self.chk_smart.setChecked(data.get("smart_compress", False))
            self.smart_kb_entry.setText(data.get("target_kb", "500"))
            self.entry_width.setText(data.get("resize_width", ""))
            self.entry_height.setText(data.get("resize_height", ""))
            self.resize_mode_combo.setCurrentText(data.get("resize_mode", "Stretch"))
            self.chk_gray.setChecked(data.get("filter_gray", False))
            self.chk_auto.setChecked(data.get("filter_auto", False))
            self.chk_sharp.setChecked(data.get("filter_sharp", False))
            self.chk_blur.setChecked(data.get("filter_blur", False))
            self.chk_contour.setChecked(data.get("filter_contour", False))
            self.chk_emboss.setChecked(data.get("filter_emboss", False))
            self.chk_edge.setChecked(data.get("filter_edge", False))
            self.chk_preserve_exif.setChecked(data.get("preserve_exif", True))
            self.chk_meta_enable.setChecked(data.get("meta_enable", False))
            self.meta_author.setText(data.get("meta_author", ""))
            self.meta_copyright.setText(data.get("meta_copyright", ""))
            self.meta_desc.setText(data.get("meta_description", ""))
            self.adj_brightness.setValue(data.get("adj_brightness", 10))
            self.adj_contrast.setValue(data.get("adj_contrast", 10))
            self.adj_saturation.setValue(data.get("adj_saturation", 10))
            self.adj_sharpness.setValue(data.get("adj_sharpness", 10))
            self.wm_pos_combo.setCurrentText(data.get("wm_pos", "Bottom Right"))
            self.wm_size_slider.setValue(data.get("wm_size", 15))
            self.wm_opacity_slider.setValue(data.get("wm_opacity", 100))
            self.wm_mx.setText(data.get("wm_margin_x", "10"))
            self.wm_my.setText(data.get("wm_margin_y", "10"))
            self.trigger_preview_update()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load preset: {e}")

    def _handle_preview_ready(self, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.preview_canvas.set_pixmap(pixmap)

    def _handle_thumbnail_loaded(self, row, qimage):
        pixmap = QPixmap.fromImage(qimage)
        self.queue_model.set_thumbnail(row, pixmap)

    def set_preview_image(self, filepath):
        self.current_preview_file = filepath
        
        def load_cache_task():
            try:
                im = Image.open(filepath)
                im = ImageOps.exif_transpose(im)
                im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                self._cached_preview_image = im
                self._cached_preview_path = filepath
                self.preview_cache_ready.emit()
            except:
                self.preview_cache_ready.emit()
        threading.Thread(target=load_cache_task, daemon=True).start()

    def trigger_preview_update(self):
        if not self.current_preview_file: return
        self.last_preview_time = time.time()
        self.preview_timer.stop()
        self.preview_timer.start(250)

    def _process_preview(self):
        if time.time() - self.last_preview_time < 0.2:
            self.preview_timer.start(100)
            return
            
        params = self._get_current_params()
        
        try:
            w_str, h_str = params["res_w_str"], params["res_h_str"]
            params["resize"] = get_resize_dimensions((1000, 1000), w_str, h_str)
        except:
            params["resize"] = None

        def task():
            try:
                if self._cached_preview_path == self.current_preview_file and self._cached_preview_image is not None:
                    im = self._cached_preview_image.copy()
                else:
                    im = Image.open(self.current_preview_file)
                    im = ImageOps.exif_transpose(im)
                    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                
                preview_size = (400, 400)
                
                try:
                    w_str, h_str = params["res_w_str"], params["res_h_str"]
                    res_dim = get_resize_dimensions(im.size, w_str, h_str)
                    if res_dim:
                        if params["mode"] == "Fit (Maintain AR)": im = ImageOps.contain(im, res_dim, Image.Resampling.LANCZOS)
                        elif params["mode"] == "Fill/Crop": im = ImageOps.fit(im, res_dim, Image.Resampling.LANCZOS)
                        else: im = im.resize(res_dim, Image.Resampling.LANCZOS)
                except: pass

                im.thumbnail(preview_size, Image.Resampling.LANCZOS)
                
                if params["f_gray"]: im = im.convert("L")
                if params["f_auto"]:
                    try: im = ImageOps.autocontrast(im.convert("RGB"))
                    except: pass
                if params["f_sharp"]: im = im.filter(ImageFilter.SHARPEN)
                if params["f_blur"]: im = im.filter(ImageFilter.BLUR)
                if params["f_contour"]: im = im.filter(ImageFilter.CONTOUR)
                if params["f_emboss"]: im = im.filter(ImageFilter.EMBOSS)
                if params["f_edge"]: im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)

                if params["adj_b"] != 1.0: im = ImageEnhance.Brightness(im).enhance(params["adj_b"])
                if params["adj_c"] != 1.0: im = ImageEnhance.Contrast(im).enhance(params["adj_c"])
                if params["adj_s"] != 1.0: im = ImageEnhance.Color(im).enhance(params["adj_s"])
                if params["adj_sh"] != 1.0: im = ImageEnhance.Sharpness(im).enhance(params["adj_sh"])
                
                im = apply_watermark(im, params)
                
                im_rgb = im.convert("RGBA")
                data = im_rgb.tobytes("raw", "RGBA")
                qimage = QImage(data, im_rgb.size[0], im_rgb.size[1], QImage.Format_RGBA8888).copy()
                
                self.preview_ready.emit(qimage)
            except Exception as e:
                pass
                
        self.preview_thread = threading.Thread(target=task, daemon=True)
        self.preview_thread.start()

    def _async_load_thumb(self, filepath, row):
        def load_task():
            try:
                with Image.open(filepath) as im:
                    im = ImageOps.exif_transpose(im)
                    im.thumbnail((40, 40), Image.Resampling.LANCZOS)
                    
                    im_rgb = im.convert("RGBA")
                    data = im_rgb.tobytes("raw", "RGBA")
                    qim = QImage(data, im_rgb.size[0], im_rgb.size[1], QImage.Format_RGBA8888).copy()
                    
                    self.thumbnail_loaded.emit(row, qim)
            except:
                pass
        self.thumbnail_pool.submit(load_task)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", 
            "Images (*.jpg *.jpeg *.png *.webp *.tiff *.bmp *.gif)"
        )
        if files:
            current_count = len(self.selected_files)
            for idx, filepath in enumerate(files):
                if self.queue_model.add_file(filepath):
                    self.selected_files.append(filepath)
                    self._async_load_thumb(filepath, current_count + idx)
            
            self.update_queue_selection()

    def clear_files(self):
        self.selected_files.clear()
        self.queue_model.clear()
        self.current_preview_file = None
        self._cached_preview_image = None
        self._cached_preview_path = None
        self.preview_canvas.scene.clear()
        self.preview_canvas.pixmap_item = QGraphicsPixmapItem()
        self.preview_canvas.scene.addItem(self.preview_canvas.pixmap_item)

    def select_watermark(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Logo (PNG)", "", "PNG Files (*.png)")
        if file:
            self.entry_wm_path.setText(file)
            self.trigger_preview_update()

    def select_favicon_source(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Source Image", "", 
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if file:
            self.favicon_source = file
            self.favicon_src_entry.setText(Path(file).name)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_entry.setText(folder)

    def update_queue_selection(self):
        if not self.current_preview_file and self.selected_files:
            self.set_preview_image(self.selected_files[0])
            idx = self.queue_model.index(0, 0)
            self.queue_view.setCurrentIndex(idx)
        elif self.current_preview_file in self.selected_files:
            idx_num = self.selected_files.index(self.current_preview_file)
            idx = self.queue_model.index(idx_num, 0)
            self.queue_view.setCurrentIndex(idx)

    def _get_current_params(self):
        return {
            "fmt": self.out_format_combo.currentText(),
            "qual": self.quality_slider.value(),
            "exif": self.chk_preserve_exif.isChecked(),
            "out_dir": Path(self.output_folder_entry.text()) if self.output_folder_entry.text() else None,
            "mode": self.resize_mode_combo.currentText(),
            "wm": self.entry_wm_path.text(),
            "wm_pos": self.wm_pos_combo.currentText(),
            "wm_size": self.wm_size_slider.value() / 100.0,
            "wm_opacity": self.wm_opacity_slider.value() / 100.0,
            "wm_margin_x": parse_int(self.wm_mx.text(), 10),
            "wm_margin_y": parse_int(self.wm_my.text(), 10),
            "pref": self.rename_prefix.text().strip(),
            "suff": self.rename_suffix.text().strip(),
            "f_gray": self.chk_gray.isChecked(),
            "f_auto": self.chk_auto.isChecked(),
            "f_sharp": self.chk_sharp.isChecked(),
            "f_blur": self.chk_blur.isChecked(),
            "f_contour": self.chk_contour.isChecked(),
            "f_emboss": self.chk_emboss.isChecked(),
            "f_edge": self.chk_edge.isChecked(),
            "adj_b": self.adj_brightness.value() / 10.0,
            "adj_c": self.adj_contrast.value() / 10.0,
            "adj_s": self.adj_saturation.value() / 10.0,
            "adj_sh": self.adj_sharpness.value() / 10.0,
            "smart": self.chk_smart.isChecked(),
            "target_kb": int(self.smart_kb_entry.text()) if self.smart_kb_entry.text().isdigit() else 500,
            "meta_en": self.chk_meta_enable.isChecked(),
            "meta_auth": self.meta_author.text(),
            "meta_copy": self.meta_copyright.text().strip(),
            "meta_desc": self.meta_desc.text().strip(),
            "res_w_str": self.entry_width.text().strip(),
            "res_h_str": self.entry_height.text().strip(),
        }

    def start_conversion(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Validation Error", "No files selected in Queue!")
            return
            
        out_dir_str = self.output_folder_entry.text().strip()
        if not out_dir_str:
            QMessageBox.warning(self, "Validation Error", "Please select an output folder first!")
            return
            
        out_dir = Path(out_dir_str)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            test_file = out_dir / f".test_write_{int(time.time())}"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Cannot write to output folder!\nDetails: {e}")
            self.reset_conversion_ui()
            return

        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("⚙️ Processing...")
        self.status_label.setText("Processing...")
        self.progress_bar.setValue(0)
        
        params = self._get_current_params()
        
        threading.Thread(target=self.convert_all, args=(params,), daemon=True).start()

    def convert_all(self, p):
        total = len(self.selected_files)
        done = 0
        
        def process_single(idx, fp):
            self.queue_model.update_progress(fp, 10, "processing")
            
            in_p = Path(fp)
            ext = "jpg" if p["fmt"] == "JPEG" else p["fmt"].lower()
            
            new_name = in_p.stem
            if p["pref"] or p["suff"]:
                pref_part = f"{p['pref']}_" if p["pref"] else ""
                suff_part = f"_{p['suff']}" if p["suff"] else ""
                new_name = f"{pref_part}{in_p.stem}_{idx:03d}{suff_part}"
                
            out_p = p["out_dir"] / f"{new_name}.{ext}"
            
            res = convert_image(
                input_path=str(in_p), output_path=str(out_p), p=p
            )
            return fp, res

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_single, i+1, fp) for i, fp in enumerate(self.selected_files)]
            
            for future in concurrent.futures.as_completed(futures):
                fp, res = future.result()
                done += 1
                progress_ratio = done / total
                
                self.progress_updated.emit(fp, 1.0 if res["success"] else -1.0)
                
                QTimer.singleShot(0, lambda d=done: self.animate_progress(int(progress_ratio * 100)))
                QTimer.singleShot(0, lambda d=done, t=total: self.status_label.setText(f"Processing ({d}/{t})..."))

        self.batch_finished.emit()

    def animate_progress(self, target_value):
        self.prog_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.prog_anim.setDuration(180)
        self.prog_anim.setStartValue(self.progress_bar.value())
        self.prog_anim.setEndValue(target_value)
        self.prog_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.prog_anim.start()

    def _update_file_progress(self, filepath, val):
        status = "success" if val > 0 else "failed"
        self.queue_model.update_progress(filepath, 100, status)

    def finish_conversion(self):
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("🚀 START PROCESSING")
        self.status_label.setText("Finished!")
        QMessageBox.information(self, "Success", "All tasks finished!")

    def reset_conversion_ui(self):
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("🚀 START PROCESSING")
        self.status_label.setText("Ready")

    def export_pdf(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "No files selected in Queue!")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not save_path:
            return
            
        self.status_label.setText("Generating PDF...")
        
        def task():
            try:
                images = []
                for fp in self.selected_files:
                    img = Image.open(fp)
                    img = ImageOps.exif_transpose(img)
                    
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        bg.paste(img, mask=img.convert("RGBA").split()[-1])
                        img = bg
                    else:
                        img = img.convert('RGB')
                        
                    images.append(img)
                    
                if images:
                    images[0].save(save_path, save_all=True, append_images=images[1:])
                
                QTimer.singleShot(0, lambda: self.status_label.setText("Ready"))
                QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", "PDF created successfully!"))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.status_label.setText("Ready"))
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(e)))
                
        threading.Thread(target=task, daemon=True).start()

    def generate_icon(self):
        if not self.favicon_source or not os.path.exists(self.favicon_source):
            QMessageBox.warning(self, "Warning", "Please select a valid source image!")
            return

        selected_sizes = [s for s, chk in self.size_checkboxes.items() if chk.isChecked()]
        if not selected_sizes:
            QMessageBox.warning(self, "Warning", "Please select at least one size!")
            return

        base_name = "favicon" if self.icon_type_combo.currentText() == "Favicon (Web)" else "app-icon"
        save_folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if not save_folder: return

        save_folder = Path(save_folder)
        self.status_label.setText("Generating Icons...")

        def task():
            try:
                with Image.open(self.favicon_source) as img:
                    base_img = img.convert("RGBA")
                    ico_images, ico_sizes = [], []

                    for size in selected_sizes:
                        resized = base_img.resize(size, Image.Resampling.LANCZOS)
                        resized.save(save_folder / f"{base_name}-{size[0]}x{size[1]}.png", "PNG")
                        ico_images.append(resized.convert("RGB") if size[0] <= 48 else resized)
                        ico_sizes.append(size)

                    if ico_images:
                        ico_images[0].save(save_folder / f"{base_name}.ico", format='ICO', append_images=ico_images[1:], sizes=ico_sizes)

                QTimer.singleShot(0, lambda: self.status_label.setText("Icon generation complete!"))
                QTimer.singleShot(0, lambda: QMessageBox.information(self, "Success", "Icons generated successfully!"))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.status_label.setText("Error!"))
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(e)))

        threading.Thread(target=task, daemon=True).start()