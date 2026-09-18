import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QTimer, QModelIndex, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox, QCheckBox,
    QSlider, QProgressBar, QListView, QFileDialog, QMessageBox,
    QStackedWidget, QGridLayout, QSizePolicy
)
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QDragEnterEvent, QDropEvent, QCloseEvent
)

from config import (
    APP_NAME, APP_VERSION, APP_AUTHOR, APP_DESCRIPTION, APP_GITHUB,
    LOGO_IMAGE_PATH, WINDOW_ICON_PATH, QSS_STYLE,
    SUPPORTED_FORMATS, RESIZE_MODES, WATERMARK_POSITIONS
)
from models.queue_model import QueueModel
from models.conversion_settings import ConversionSettings
from views.widgets import GraphicsPreviewView, SmoothScrollArea, QueueDelegate
from workers.conversion_worker import BatchConversionWorker
from workers.preview_worker import PreviewWorker
from workers.pdf_worker import PdfWorker
from core.icon_builder import generate_ico
from utils.logging import get_logger
from utils.paths import get_asset_path

logger = get_logger("MainWindow")

VALID_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".bmp", ".tiff", ".tif", ".ico"
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.resize(1280, 840)
        self.setMinimumSize(1020, 680)

        # Application Icon
        icon_path = Path(WINDOW_ICON_PATH)
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # State variables
        self.queue_model = QueueModel(self)
        self.current_preview_file: Optional[str] = None
        self._cached_preview_pil = None
        self._cached_preview_path: Optional[str] = None
        self.preview_request_id = 0

        # Workers
        self.conversion_worker: Optional[BatchConversionWorker] = None
        self.preview_worker: Optional[PreviewWorker] = None
        self.pdf_worker: Optional[PdfWorker] = None

        # Preview debounce timer
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._trigger_preview_worker)

        # Setup UI
        self.setup_ui()
        self.setAcceptDrops(True)

        # Connect Queue signals to update counter and UI
        self.queue_model.rowsInserted.connect(self.update_queue_counter)
        self.queue_model.rowsRemoved.connect(self.update_queue_counter)
        self.queue_model.modelReset.connect(self.update_queue_counter)

        logger.info(f"{APP_NAME} v{APP_VERSION} initialized successfully.")

    # ==================== DRAG & DROP ====================
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        added_any = False
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and sub.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                        if self.queue_model.add_file(str(sub)):
                            added_any = True
            elif p.is_file() and p.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                if self.queue_model.add_file(str(p)):
                    added_any = True

        if added_any:
            if not self.current_preview_file and self.queue_model.rowCount() > 0:
                first_fp = self.queue_model.data(self.queue_model.index(0), QueueModel.FilepathRole)
                self.set_preview_file(first_fp)
        event.acceptProposedAction()

    # ==================== UI SETUP ====================
    def setup_ui(self):
        self.setStyleSheet(QSS_STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 16)
        side_layout.setSpacing(8)

        # Logo / Branding
        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(4, 4, 4, 12)
        brand_layout.setSpacing(10)

        logo_path = Path(LOGO_IMAGE_PATH)
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            brand_layout.addWidget(logo_lbl)

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(0)
        title_lbl = QLabel(APP_NAME)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        sub_lbl = QLabel(f"v{APP_VERSION}")
        sub_lbl.setStyleSheet("font-size: 11px; color: #0A84FF; font-weight: 600;")
        brand_text_layout.addWidget(title_lbl)
        brand_text_layout.addWidget(sub_lbl)
        brand_layout.addLayout(brand_text_layout)
        brand_layout.addStretch()
        side_layout.addLayout(brand_layout)

        # Nav Buttons
        self.btn_nav_batch = QPushButton("🗂  Batch Converter")
        self.btn_nav_batch.setObjectName("SidebarBtn")
        self.btn_nav_batch.setCheckable(True)
        self.btn_nav_batch.setChecked(True)
        self.btn_nav_batch.clicked.connect(lambda: self.switch_view(0))
        side_layout.addWidget(self.btn_nav_batch)

        self.btn_nav_pdf = QPushButton("📄  PDF Builder")
        self.btn_nav_pdf.setObjectName("SidebarBtn")
        self.btn_nav_pdf.setCheckable(True)
        self.btn_nav_pdf.clicked.connect(lambda: self.switch_view(1))
        side_layout.addWidget(self.btn_nav_pdf)

        self.btn_nav_icon = QPushButton("🎨  Icon Generator")
        self.btn_nav_icon.setObjectName("SidebarBtn")
        self.btn_nav_icon.setCheckable(True)
        self.btn_nav_icon.clicked.connect(lambda: self.switch_view(2))
        side_layout.addWidget(self.btn_nav_icon)

        self.btn_nav_about = QPushButton("ℹ️  About Formato")
        self.btn_nav_about.setObjectName("SidebarBtn")
        self.btn_nav_about.setCheckable(True)
        self.btn_nav_about.clicked.connect(lambda: self.switch_view(3))
        side_layout.addWidget(self.btn_nav_about)

        side_layout.addStretch()

        # Quick stats footer in sidebar
        self.lbl_sidebar_info = QLabel("Native Desktop App")
        self.lbl_sidebar_info.setStyleSheet("color: #606066; font-size: 11px; padding: 4px;")
        side_layout.addWidget(self.lbl_sidebar_info)

        main_layout.addWidget(sidebar)

        # 2. Main Stacked Views
        self.view_stack = QStackedWidget()
        self.batch_view = QWidget()
        self.pdf_view = QWidget()
        self.icon_view = QWidget()
        self.about_view = QWidget()

        self.setup_batch_view()
        self.setup_pdf_view()
        self.setup_icon_view()
        self.setup_about_view()

        self.view_stack.addWidget(self.batch_view)
        self.view_stack.addWidget(self.pdf_view)
        self.view_stack.addWidget(self.icon_view)
        self.view_stack.addWidget(self.about_view)

        main_layout.addWidget(self.view_stack)

    def switch_view(self, index: int):
        self.btn_nav_batch.setChecked(index == 0)
        self.btn_nav_pdf.setChecked(index == 1)
        self.btn_nav_icon.setChecked(index == 2)
        self.btn_nav_about.setChecked(index == 3)
        self.view_stack.setCurrentIndex(index)

    def create_card(self, parent_layout: QVBoxLayout, title: str) -> QVBoxLayout:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

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

    # ==================== BATCH CONVERTER VIEW ====================
    def setup_batch_view(self):
        layout = QHBoxLayout(self.batch_view)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left Column: Queue & Live Preview
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        # Queue Card
        queue_card = QFrame()
        queue_card.setObjectName("Card")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(14, 14, 14, 14)
        queue_layout.setSpacing(10)

        queue_hdr = QHBoxLayout()
        self.queue_title = QLabel("Queue · 0 Files")
        self.queue_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        queue_hdr.addWidget(self.queue_title)

        self.queue_subtitle = QLabel("(Drag & Drop Supported)")
        self.queue_subtitle.setStyleSheet("color: #7C7C82; font-size: 12px;")
        queue_hdr.addWidget(self.queue_subtitle)

        queue_hdr.addStretch()
        queue_layout.addLayout(queue_hdr)

        self.queue_view = QListView()
        self.queue_view.setModel(self.queue_model)
        self.queue_view.setItemDelegate(QueueDelegate(self))
        self.queue_view.clicked.connect(self.handle_queue_click)
        queue_layout.addWidget(self.queue_view, stretch=1)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Files")
        self.btn_add.clicked.connect(self.add_files_dialog)
        self.btn_clear = QPushButton("🗑 Clear Queue")
        self.btn_clear.clicked.connect(self.clear_queue)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_clear)
        queue_layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        queue_layout.addWidget(self.progress_bar)

        left_layout.addWidget(queue_card, stretch=6)

        # Preview Card
        preview_card = QFrame()
        preview_card.setObjectName("Card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(10)

        p_title = QLabel("Live Preview (Drag to Pan / Scroll to Zoom)")
        p_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        preview_layout.addWidget(p_title)

        self.preview_canvas = GraphicsPreviewView()
        preview_layout.addWidget(self.preview_canvas, stretch=1)

        left_layout.addWidget(preview_card, stretch=5)
        layout.addWidget(left_col, stretch=6)

        # Right Column: Settings Panel (Scrollable)
        self.right_scroll = SmoothScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setMinimumWidth(430)
        self.right_scroll.setMaximumWidth(460)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 0, 12, 10)
        right_layout.setSpacing(14)

        # Header Bar
        top_hdr = QHBoxLayout()
        ws_title = QLabel("Workspace Settings")
        ws_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        top_hdr.addWidget(ws_title)
        top_hdr.addStretch()

        self.btn_reset_all = QPushButton("🔄 Reset Settings")
        self.btn_reset_all.clicked.connect(self.reset_all_settings)
        top_hdr.addWidget(self.btn_reset_all)
        right_layout.addLayout(top_hdr)

        # Card 1: Output Format & Compression
        card_fmt = self.create_card(right_layout, "Output Format & Compression")
        self.combo_format = QComboBox()
        self.combo_format.addItems(list(SUPPORTED_FORMATS))
        self.combo_format.setCurrentText("WEBP")
        self.combo_format.currentTextChanged.connect(self.on_settings_changed)
        card_fmt.addWidget(self.combo_format)

        qual_row = QHBoxLayout()
        qual_row.addWidget(QLabel("Quality"))
        self.lbl_qual_val = QLabel("85%")
        self.lbl_qual_val.setStyleSheet("color: #0A84FF; font-weight: bold;")
        qual_row.addStretch()
        qual_row.addWidget(self.lbl_qual_val)
        card_fmt.addLayout(qual_row)

        self.slider_qual = QSlider(Qt.Horizontal)
        self.slider_qual.setRange(1, 100)
        self.slider_qual.setValue(85)
        self.slider_qual.valueChanged.connect(self._on_qual_slider_changed)
        card_fmt.addWidget(self.slider_qual)

        self.chk_smart_comp = QCheckBox("Smart Compression (Target File Size)")
        self.chk_smart_comp.stateChanged.connect(self.on_settings_changed)
        card_fmt.addWidget(self.chk_smart_comp)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target Size (KB):"))
        self.entry_target_kb = QLineEdit("150")
        self.entry_target_kb.setFixedWidth(100)
        self.entry_target_kb.textChanged.connect(self.on_settings_changed)
        target_row.addWidget(self.entry_target_kb)
        target_row.addStretch()
        card_fmt.addLayout(target_row)

        # Card 2: Dimensions & Resizing
        card_res = self.create_card(right_layout, "Dimensions & Resizing")
        dim_row = QHBoxLayout()
        dim_row.addWidget(QLabel("Width:"))
        self.entry_width = QLineEdit()
        self.entry_width.setPlaceholderText("Auto")
        self.entry_width.textChanged.connect(self.on_settings_changed)
        dim_row.addWidget(self.entry_width)

        dim_row.addWidget(QLabel("Height:"))
        self.entry_height = QLineEdit()
        self.entry_height.setPlaceholderText("Auto")
        self.entry_height.textChanged.connect(self.on_settings_changed)
        dim_row.addWidget(self.entry_height)
        card_res.addLayout(dim_row)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Resize Mode:"))
        self.combo_resize_mode = QComboBox()
        self.combo_resize_mode.addItems(list(RESIZE_MODES))
        self.combo_resize_mode.currentTextChanged.connect(self.on_settings_changed)
        mode_row.addWidget(self.combo_resize_mode)
        card_res.addLayout(mode_row)

        # Card 3: Color Adjustments & Tuning
        card_adj = self.create_card(right_layout, "Color Adjustments & Tuning")
        self.slider_brightness = self._add_slider_row(card_adj, "Brightness", 10, 250, 100)
        self.slider_contrast = self._add_slider_row(card_adj, "Contrast", 10, 250, 100)
        self.slider_saturation = self._add_slider_row(card_adj, "Saturation", 0, 250, 100)
        self.slider_sharpness = self._add_slider_row(card_adj, "Sharpness", 0, 300, 100)

        # Card 4: Artistic & Utility Filters
        card_filt = self.create_card(right_layout, "Artistic & Utility Filters")
        filt_grid = QGridLayout()
        self.chk_gray = QCheckBox("Grayscale")
        self.chk_auto = QCheckBox("Auto Contrast")
        self.chk_sharp = QCheckBox("Sharpen")
        self.chk_blur = QCheckBox("Blur")
        self.chk_contour = QCheckBox("Contour")
        self.chk_emboss = QCheckBox("Emboss")
        self.chk_edge = QCheckBox("Edge Enhance")

        for chk in (self.chk_gray, self.chk_auto, self.chk_sharp, self.chk_blur,
                    self.chk_contour, self.chk_emboss, self.chk_edge):
            chk.stateChanged.connect(self.on_settings_changed)

        filt_grid.addWidget(self.chk_gray, 0, 0)
        filt_grid.addWidget(self.chk_auto, 0, 1)
        filt_grid.addWidget(self.chk_sharp, 1, 0)
        filt_grid.addWidget(self.chk_blur, 1, 1)
        filt_grid.addWidget(self.chk_contour, 2, 0)
        filt_grid.addWidget(self.chk_emboss, 2, 1)
        filt_grid.addWidget(self.chk_edge, 3, 0)
        card_filt.addLayout(filt_grid)

        # Card 5: Visual Watermarking
        card_wm = self.create_card(right_layout, "Visual Watermarking")
        wm_file_row = QHBoxLayout()
        self.entry_wm_path = QLineEdit()
        self.entry_wm_path.setPlaceholderText("No watermark image selected")
        self.entry_wm_path.setReadOnly(True)
        self.btn_select_wm = QPushButton("📁 Browse")
        self.btn_select_wm.clicked.connect(self.select_watermark_dialog)
        self.btn_clear_wm = QPushButton("×")
        self.btn_clear_wm.setFixedWidth(28)
        self.btn_clear_wm.clicked.connect(self.clear_watermark)
        wm_file_row.addWidget(self.entry_wm_path)
        wm_file_row.addWidget(self.btn_select_wm)
        wm_file_row.addWidget(self.btn_clear_wm)
        card_wm.addLayout(wm_file_row)

        wm_pos_row = QHBoxLayout()
        wm_pos_row.addWidget(QLabel("Position:"))
        self.combo_wm_pos = QComboBox()
        self.combo_wm_pos.addItems(list(WATERMARK_POSITIONS))
        self.combo_wm_pos.setCurrentText("Bottom Right")
        self.combo_wm_pos.currentTextChanged.connect(self.on_settings_changed)
        wm_pos_row.addWidget(self.combo_wm_pos)
        card_wm.addLayout(wm_pos_row)

        self.slider_wm_scale = self._add_slider_row(card_wm, "Size Scale", 5, 100, 20)
        self.slider_wm_opacity = self._add_slider_row(card_wm, "Opacity", 5, 100, 75)

        wm_margin_row = QHBoxLayout()
        wm_margin_row.addWidget(QLabel("Margin X:"))
        self.entry_wm_mx = QLineEdit("15")
        self.entry_wm_mx.textChanged.connect(self.on_settings_changed)
        wm_margin_row.addWidget(self.entry_wm_mx)
        wm_margin_row.addWidget(QLabel("Margin Y:"))
        self.entry_wm_my = QLineEdit("15")
        self.entry_wm_my.textChanged.connect(self.on_settings_changed)
        wm_margin_row.addWidget(self.entry_wm_my)
        card_wm.addLayout(wm_margin_row)

        # Card 6: Metadata & EXIF Options
        card_meta = self.create_card(right_layout, "Metadata & EXIF Options")
        self.chk_preserve_exif = QCheckBox("Preserve Original EXIF / Metadata")
        self.chk_preserve_exif.setChecked(True)
        self.chk_preserve_exif.stateChanged.connect(self.on_settings_changed)
        card_meta.addWidget(self.chk_preserve_exif)

        self.chk_inject_meta = QCheckBox("Inject Custom Metadata (Author, Copyright)")
        self.chk_inject_meta.stateChanged.connect(self.on_settings_changed)
        card_meta.addWidget(self.chk_inject_meta)

        self.entry_meta_author = QLineEdit()
        self.entry_meta_author.setPlaceholderText("Author / Artist")
        self.entry_meta_author.textChanged.connect(self.on_settings_changed)
        card_meta.addWidget(self.entry_meta_author)

        self.entry_meta_copy = QLineEdit()
        self.entry_meta_copy.setPlaceholderText("Copyright Notice")
        self.entry_meta_copy.textChanged.connect(self.on_settings_changed)
        card_meta.addWidget(self.entry_meta_copy)

        self.entry_meta_desc = QLineEdit()
        self.entry_meta_desc.setPlaceholderText("Description")
        self.entry_meta_desc.textChanged.connect(self.on_settings_changed)
        card_meta.addWidget(self.entry_meta_desc)

        # Card 7: Presets & Configurations
        card_preset = self.create_card(right_layout, "Presets & Configurations")
        preset_btn_row = QHBoxLayout()
        self.btn_save_preset = QPushButton("💾 Save Preset")
        self.btn_save_preset.clicked.connect(self.save_preset_dialog)
        self.btn_load_preset = QPushButton("📂 Load Preset")
        self.btn_load_preset.clicked.connect(self.load_preset_dialog)
        preset_btn_row.addWidget(self.btn_save_preset)
        preset_btn_row.addWidget(self.btn_load_preset)
        card_preset.addLayout(preset_btn_row)

        # Card 8: File Naming & Output Destination
        card_dest = self.create_card(right_layout, "File Naming & Output Destination")
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Prefix:"))
        self.entry_prefix = QLineEdit()
        self.entry_prefix.setPlaceholderText("e.g. thumb")
        name_row.addWidget(self.entry_prefix)

        name_row.addWidget(QLabel("Suffix:"))
        self.entry_suffix = QLineEdit()
        self.entry_suffix.setPlaceholderText("e.g. min")
        name_row.addWidget(self.entry_suffix)
        card_dest.addLayout(name_row)

        out_row = QHBoxLayout()
        self.entry_out_dir = QLineEdit()
        self.entry_out_dir.setPlaceholderText("Select destination folder...")
        self.btn_browse_out = QPushButton("📁 Output Folder")
        self.btn_browse_out.clicked.connect(self.choose_output_folder_dialog)
        out_row.addWidget(self.entry_out_dir)
        out_row.addWidget(self.btn_browse_out)
        card_dest.addLayout(out_row)

        # Bottom Conversion Action Bar
        action_card = QFrame()
        action_card.setObjectName("Card")
        action_card.setStyleSheet("background-color: #17171A; border: 1px solid #282830;")
        act_layout = QVBoxLayout(action_card)
        act_layout.setContentsMargins(14, 14, 14, 14)
        act_layout.setSpacing(10)

        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #0A84FF; font-weight: 600; font-size: 13px;")
        act_layout.addWidget(self.lbl_status)

        btn_action_row = QHBoxLayout()
        self.btn_convert = QPushButton("🚀 START PROCESSING")
        self.btn_convert.setObjectName("PrimaryBtn")
        self.btn_convert.setFixedHeight(44)
        self.btn_convert.clicked.connect(self.start_batch_conversion)
        btn_action_row.addWidget(self.btn_convert, stretch=3)

        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.setFixedHeight(44)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_batch_conversion)
        btn_action_row.addWidget(self.btn_cancel, stretch=1)
        act_layout.addLayout(btn_action_row)

        right_layout.addWidget(action_card)

        self.right_scroll.setWidget(right_container)
        layout.addWidget(self.right_scroll)

    def _add_slider_row(self, layout: QVBoxLayout, name: str, min_val: int, max_val: int, default_val: int) -> QSlider:
        row = QHBoxLayout()
        row.addWidget(QLabel(name))
        lbl_val = QLabel(f"{default_val}%")
        lbl_val.setStyleSheet("color: #7C7C82; font-weight: bold; font-size: 11px;")
        row.addStretch()
        row.addWidget(lbl_val)
        layout.addLayout(row)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(lambda v: lbl_val.setText(f"{v}%"))
        slider.valueChanged.connect(self.on_settings_changed)
        layout.addWidget(slider)
        return slider

    def _on_qual_slider_changed(self, v: int):
        self.lbl_qual_val.setText(f"{v}%")
        self.on_settings_changed()

    # ==================== PDF BUILDER VIEW ====================
    def setup_pdf_view(self):
        layout = QVBoxLayout(self.pdf_view)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(620, 520)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(36, 32, 36, 32)
        c_lay.setSpacing(16)
        c_lay.setAlignment(Qt.AlignCenter)

        title = QLabel("📄 Multi-Page PDF Builder")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        c_lay.addWidget(title)

        desc = QLabel("Assemble all images in your Queue into a polished multi-page PDF document.")
        desc.setStyleSheet("color: #9A9A9F; font-size: 13px;")
        desc.setWordWrap(True)
        c_lay.addWidget(desc)

        opt_grid = QGridLayout()
        opt_grid.setHorizontalSpacing(16)
        opt_grid.setVerticalSpacing(10)

        opt_grid.addWidget(QLabel("Page Format:"), 0, 0)
        self.combo_pdf_size = QComboBox()
        self.combo_pdf_size.addItems(["A4", "A5", "Letter", "Original"])
        opt_grid.addWidget(self.combo_pdf_size, 0, 1)

        opt_grid.addWidget(QLabel("Orientation:"), 1, 0)
        self.combo_pdf_orient = QComboBox()
        self.combo_pdf_orient.addItems(["Portrait", "Landscape"])
        opt_grid.addWidget(self.combo_pdf_orient, 1, 1)

        opt_grid.addWidget(QLabel("Fit Mode:"), 2, 0)
        self.combo_pdf_fit = QComboBox()
        self.combo_pdf_fit.addItems(["Fit", "Fill"])
        opt_grid.addWidget(self.combo_pdf_fit, 2, 1)

        opt_grid.addWidget(QLabel("Page Margin (pt):"), 3, 0)
        self.entry_pdf_margin = QLineEdit("20")
        self.entry_pdf_margin.setFixedWidth(80)
        opt_grid.addWidget(self.entry_pdf_margin, 3, 1)

        c_lay.addLayout(opt_grid)

        self.lbl_pdf_status = QLabel("Ready to export images from Queue")
        self.lbl_pdf_status.setStyleSheet("color: #7C7C82; font-size: 12px;")
        c_lay.addWidget(self.lbl_pdf_status)

        self.btn_export_pdf = QPushButton("Export to PDF")
        self.btn_export_pdf.setObjectName("PrimaryBtn")
        self.btn_export_pdf.setFixedHeight(48)
        self.btn_export_pdf.setFixedWidth(220)
        self.btn_export_pdf.clicked.connect(self.start_pdf_export)
        c_lay.addWidget(self.btn_export_pdf)

        layout.addWidget(card)

    # ==================== ICON GENERATOR VIEW ====================
    def setup_icon_view(self):
        layout = QVBoxLayout(self.icon_view)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(620, 520)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(36, 32, 36, 32)
        c_lay.setSpacing(14)
        c_lay.setAlignment(Qt.AlignCenter)

        title = QLabel("🎨 Icon & Favicon Generator")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        c_lay.addWidget(title)

        desc = QLabel("Generate multi-resolution Windows .ico or web favicon assets from a single master image.")
        desc.setStyleSheet("color: #9A9A9F; font-size: 13px;")
        desc.setWordWrap(True)
        c_lay.addWidget(desc)

        src_row = QHBoxLayout()
        self.entry_icon_src = QLineEdit()
        self.entry_icon_src.setPlaceholderText("No source image selected")
        self.entry_icon_src.setReadOnly(True)
        self.btn_pick_icon_src = QPushButton("📁 Browse")
        self.btn_pick_icon_src.clicked.connect(self.select_icon_source_dialog)
        src_row.addWidget(self.entry_icon_src)
        src_row.addWidget(self.btn_pick_icon_src)
        c_lay.addLayout(src_row)

        sizes_box = QFrame()
        sizes_box.setStyleSheet("background-color: #121214; border: 1px solid #202024; border-radius: 6px;")
        sizes_grid = QGridLayout(sizes_box)
        sizes_grid.setContentsMargins(12, 12, 12, 12)
        sizes_grid.setSpacing(8)

        self.icon_size_checks = {}
        all_sizes = [16, 32, 48, 64, 128, 256]
        for i, sz in enumerate(all_sizes):
            chk = QCheckBox(f"{sz}×{sz} px")
            chk.setChecked(True)
            sizes_grid.addWidget(chk, i // 3, i % 3)
            self.icon_size_checks[sz] = chk

        c_lay.addWidget(sizes_box)

        self.lbl_icon_status = QLabel("Ready")
        self.lbl_icon_status.setStyleSheet("color: #7C7C82; font-size: 12px;")
        c_lay.addWidget(self.lbl_icon_status)

        self.btn_generate_ico = QPushButton("⚡ Generate .ICO")
        self.btn_generate_ico.setObjectName("PrimaryBtn")
        self.btn_generate_ico.setFixedHeight(48)
        self.btn_generate_ico.setFixedWidth(220)
        self.btn_generate_ico.clicked.connect(self.start_icon_export)
        c_lay.addWidget(self.btn_generate_ico)

        layout.addWidget(card)

    # ==================== ABOUT VIEW ====================
    def setup_about_view(self):
        layout = QVBoxLayout(self.about_view)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(620, 520)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(36, 36, 36, 36)
        c_lay.setSpacing(14)
        c_lay.setAlignment(Qt.AlignCenter)

        logo_path = Path(LOGO_IMAGE_PATH)
        if logo_path.exists():
            logo_lbl = QLabel()
            pix = QPixmap(str(logo_path)).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            c_lay.addWidget(logo_lbl)

        name_lbl = QLabel(f"{APP_NAME} Desktop")
        name_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        c_lay.addWidget(name_lbl)

        ver_lbl = QLabel(f"Version {APP_VERSION} (Native Python & Qt6)")
        ver_lbl.setStyleSheet("font-size: 13px; color: #0A84FF; font-weight: 600;")
        c_lay.addWidget(ver_lbl)

        desc_lbl = QLabel(APP_DESCRIPTION)
        desc_lbl.setStyleSheet("color: #CCCCCC; font-size: 13px;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        c_lay.addWidget(desc_lbl)

        info_box = QFrame()
        info_box.setStyleSheet("background-color: #121214; border: 1px solid #202024; border-radius: 6px; padding: 10px;")
        i_lay = QVBoxLayout(info_box)
        i_lay.setSpacing(6)

        author_lbl = QLabel(f"Author: {APP_AUTHOR}")
        author_lbl.setStyleSheet("color: #E2E2E6; font-size: 12px;")
        i_lay.addWidget(author_lbl)

        github_lbl = QLabel(f"GitHub: {APP_GITHUB}")
        github_lbl.setStyleSheet("color: #0A84FF; font-size: 12px;")
        i_lay.addWidget(github_lbl)

        lic_lbl = QLabel("License: Open Source (MIT)")
        lic_lbl.setStyleSheet("color: #7C7C82; font-size: 12px;")
        i_lay.addWidget(lic_lbl)

        c_lay.addWidget(info_box)
        layout.addWidget(card)

    # ==================== QUEUE INTERACTIONS ====================
    def update_queue_counter(self, *args):
        count = self.queue_model.rowCount()
        file_text = "1 File" if count == 1 else f"{count} Files"
        self.queue_title.setText(f"Queue · {file_text}")

    def handle_queue_click(self, index: QModelIndex):
        if not index.isValid():
            return
        row = index.row()
        fp = self.queue_model.data(index, QueueModel.FilepathRole)
        if fp:
            self.set_preview_file(fp)

    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.gif *.bmp *.tiff *.tif *.ico);;All Files (*)"
        )
        if files:
            for fp in files:
                self.queue_model.add_file(fp)
            if not self.current_preview_file and self.queue_model.rowCount() > 0:
                first_fp = self.queue_model.data(self.queue_model.index(0), QueueModel.FilepathRole)
                self.set_preview_file(first_fp)

    def clear_queue(self):
        if self.conversion_worker and self.conversion_worker.isRunning():
            QMessageBox.warning(self, "Busy", "Please cancel or wait for current batch to complete before clearing.")
            return
        self.queue_model.clear()
        self.current_preview_file = None
        self._cached_preview_pil = None
        self._cached_preview_path = None
        self.preview_canvas.scene.clear()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Ready")

    # ==================== PREVIEW MANAGEMENT ====================
    def set_preview_file(self, filepath: str):
        if not filepath or not Path(filepath).exists():
            return
        self.current_preview_file = filepath
        self._cached_preview_pil = None
        self._cached_preview_path = None
        self.on_settings_changed()

    def on_settings_changed(self):
        if not self.current_preview_file:
            return
        self.preview_timer.start(180)

    def _trigger_preview_worker(self):
        if not self.current_preview_file:
            return

        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.cancel()

        self.preview_request_id += 1
        req_id = self.preview_request_id
        settings = self.get_current_settings()

        self.preview_worker = PreviewWorker(
            source_path=self.current_preview_file,
            settings=settings,
            request_id=req_id,
            cached_source_img=self._cached_preview_pil,
            parent=self
        )
        self.preview_worker.preview_ready.connect(self._on_preview_ready)
        self.preview_worker.start()

    def _on_preview_ready(self, qimage: QImage, req_id: int):
        if req_id != self.preview_request_id:
            # Stale response from older slider adjustment
            return
        pixmap = QPixmap.fromImage(qimage)
        self.preview_canvas.set_pixmap(pixmap)

    # ==================== SETTINGS & PRESETS ====================
    def get_current_settings(self) -> ConversionSettings:
        s = ConversionSettings()
        s.fmt = self.combo_format.currentText()
        s.qual = self.slider_qual.value()
        s.smart = self.chk_smart_comp.isChecked()

        try:
            s.target_kb = max(1, int(self.entry_target_kb.text().strip()))
        except Exception:
            s.target_kb = 150

        s.mode = self.combo_resize_mode.currentText()
        s.res_w_str = self.entry_width.text().strip()
        s.res_h_str = self.entry_height.text().strip()

        s.adj_b = self.slider_brightness.value() / 100.0
        s.adj_c = self.slider_contrast.value() / 100.0
        s.adj_s = self.slider_saturation.value() / 100.0
        s.adj_sh = self.slider_sharpness.value() / 100.0

        s.f_gray = self.chk_gray.isChecked()
        s.f_auto = self.chk_auto.isChecked()
        s.f_sharp = self.chk_sharp.isChecked()
        s.f_blur = self.chk_blur.isChecked()
        s.f_contour = self.chk_contour.isChecked()
        s.f_emboss = self.chk_emboss.isChecked()
        s.f_edge = self.chk_edge.isChecked()

        s.wm = self.entry_wm_path.text().strip()
        s.wm_pos = self.combo_wm_pos.currentText()
        s.wm_size = self.slider_wm_scale.value() / 100.0
        s.wm_opacity = self.slider_wm_opacity.value() / 100.0

        try:
            s.wm_margin_x = max(0, int(self.entry_wm_mx.text().strip()))
        except Exception:
            s.wm_margin_x = 15

        try:
            s.wm_margin_y = max(0, int(self.entry_wm_my.text().strip()))
        except Exception:
            s.wm_margin_y = 15

        s.exif = self.chk_preserve_exif.isChecked()
        s.meta_en = self.chk_inject_meta.isChecked()
        s.meta_auth = self.entry_meta_author.text().strip()
        s.meta_copy = self.entry_meta_copy.text().strip()
        s.meta_desc = self.entry_meta_desc.text().strip()

        s.pref = self.entry_prefix.text().strip()
        s.suff = self.entry_suffix.text().strip()
        s.out_dir = self.entry_out_dir.text().strip()

        s.validate()
        return s

    def apply_settings(self, s: ConversionSettings):
        s.validate()
        self.combo_format.setCurrentText(s.fmt)
        self.slider_qual.setValue(s.qual)
        self.chk_smart_comp.setChecked(s.smart)
        self.entry_target_kb.setText(str(s.target_kb))

        self.combo_resize_mode.setCurrentText(s.mode)
        self.entry_width.setText(s.res_w_str)
        self.entry_height.setText(s.res_h_str)

        self.slider_brightness.setValue(int(s.adj_b * 100))
        self.slider_contrast.setValue(int(s.adj_c * 100))
        self.slider_saturation.setValue(int(s.adj_s * 100))
        self.slider_sharpness.setValue(int(s.adj_sh * 100))

        self.chk_gray.setChecked(s.f_gray)
        self.chk_auto.setChecked(s.f_auto)
        self.chk_sharp.setChecked(s.f_sharp)
        self.chk_blur.setChecked(s.f_blur)
        self.chk_contour.setChecked(s.f_contour)
        self.chk_emboss.setChecked(s.f_emboss)
        self.chk_edge.setChecked(s.f_edge)

        self.entry_wm_path.setText(s.wm)
        self.combo_wm_pos.setCurrentText(s.wm_pos)
        self.slider_wm_scale.setValue(int(s.wm_size * 100))
        self.slider_wm_opacity.setValue(int(s.wm_opacity * 100))
        self.entry_wm_mx.setText(str(s.wm_margin_x))
        self.entry_wm_my.setText(str(s.wm_margin_y))

        self.chk_preserve_exif.setChecked(s.exif)
        self.chk_inject_meta.setChecked(s.meta_en)
        self.entry_meta_author.setText(s.meta_auth)
        self.entry_meta_copy.setText(s.meta_copy)
        self.entry_meta_desc.setText(s.meta_desc)

        self.on_settings_changed()

    def reset_all_settings(self):
        default = ConversionSettings()
        self.apply_settings(default)
        self.lbl_status.setText("Settings reset to defaults")

    def save_preset_dialog(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset JSON", "", "Preset Files (*.json)"
        )
        if save_path:
            try:
                s = self.get_current_settings()
                s.save_preset_file(Path(save_path))
                QMessageBox.information(self, "Preset Saved", f"Preset saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save preset: {e}")

    def load_preset_dialog(self):
        load_path, _ = QFileDialog.getOpenFileName(
            self, "Load Preset JSON", "", "Preset Files (*.json)"
        )
        if load_path:
            try:
                s = ConversionSettings.load_preset_file(Path(load_path))
                self.apply_settings(s)
                QMessageBox.information(self, "Preset Loaded", f"Loaded preset settings from:\n{load_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")

    def select_watermark_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", "", "PNG Images (*.png);;All Images (*.*)"
        )
        if path:
            self.entry_wm_path.setText(path)
            self.on_settings_changed()

    def clear_watermark(self):
        self.entry_wm_path.clear()
        self.on_settings_changed()

    def choose_output_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.entry_out_dir.setText(folder)

    # ==================== BATCH CONVERSION EXECUTION ====================
    def start_batch_conversion(self):
        filepaths = self.queue_model.get_filepaths()
        if not filepaths:
            QMessageBox.warning(self, "Queue Empty", "Please add files to the Queue before starting conversion.")
            return

        out_dir_str = self.entry_out_dir.text().strip()
        if not out_dir_str:
            QMessageBox.warning(self, "Output Required", "Please select a destination Output Folder.")
            return

        out_dir = Path(out_dir_str)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = out_dir / f".write_test_{int(time.time())}"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            QMessageBox.critical(self, "Folder Error", f"Cannot write to output folder:\n{out_dir}\nDetails: {e}")
            return

        settings = self.get_current_settings()

        # Update UI state
        self.btn_convert.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_add.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.lbl_status.setText(f"Processing (0/{len(filepaths)})...")
        self.progress_bar.setValue(0)
        self.queue_model.reset_all_status()

        # Launch thread-safe conversion worker
        self.conversion_worker = BatchConversionWorker(
            filepaths=filepaths,
            settings=settings,
            output_dir=out_dir,
            parent=self
        )
        self.conversion_worker.file_started.connect(self._on_worker_file_started)
        self.conversion_worker.file_progress.connect(self._on_worker_file_progress)
        self.conversion_worker.file_completed.connect(self._on_worker_file_completed)
        self.conversion_worker.overall_progress.connect(self._on_worker_overall_progress)
        self.conversion_worker.batch_finished.connect(self._on_worker_batch_finished)
        self.conversion_worker.start()

    def cancel_batch_conversion(self):
        if self.conversion_worker and self.conversion_worker.isRunning():
            self.lbl_status.setText("Cancelling...")
            self.btn_cancel.setEnabled(False)
            self.conversion_worker.request_cancellation()

    def _on_worker_file_started(self, fp: str):
        self.queue_model.update_file_status(fp, 15, "processing")

    def _on_worker_file_progress(self, fp: str, pct: int, status: str):
        self.queue_model.update_file_status(fp, pct, status)

    def _on_worker_file_completed(
        self, fp: str, success: bool, error: str, out_p: str,
        actual_size: int, target_size: int, target_achieved: bool, quality: int
    ):
        status = "completed" if success else ("cancelled" if error == "Cancelled" else "failed")
        self.queue_model.update_file_status(
            filepath=fp,
            progress=100,
            status=status,
            error_msg=error,
            output_path=out_p
        )

    def _on_worker_overall_progress(self, completed: int, total: int, pct: int):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"Processing ({completed}/{total})...")

    def _on_worker_batch_finished(self, success_cnt: int, fail_cnt: int, cancel_cnt: int, cancelled: bool):
        self.btn_convert.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_add.setEnabled(True)
        self.btn_clear.setEnabled(True)

        if cancelled:
            self.lbl_status.setText(f"Cancelled (Completed: {success_cnt}, Cancelled: {cancel_cnt})")
            QMessageBox.information(
                self,
                "Batch Cancelled",
                f"Conversion was cancelled.\nCompleted: {success_cnt}\nCancelled: {cancel_cnt}\nFailed: {fail_cnt}"
            )
        else:
            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"Finished (Success: {success_cnt}, Failed: {fail_cnt})")
            msg = f"Batch processing completed!\n\nSuccessful: {success_cnt}\nFailed: {fail_cnt}"
            if fail_cnt > 0:
                QMessageBox.warning(self, "Finished with Errors", msg)
            else:
                QMessageBox.information(self, "Finished", msg)

    # ==================== PDF EXPORT ====================
    def start_pdf_export(self):
        filepaths = self.queue_model.get_filepaths()
        if not filepaths:
            QMessageBox.warning(self, "Queue Empty", "Please add images to the Queue first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export Multi-Page PDF", "", "PDF Document (*.pdf)"
        )
        if not save_path:
            return

        page_size = self.combo_pdf_size.currentText()
        orientation = self.combo_pdf_orient.currentText()
        fit_mode = self.combo_pdf_fit.currentText()
        try:
            margin = max(0, int(self.entry_pdf_margin.text().strip()))
        except Exception:
            margin = 20

        self.btn_export_pdf.setEnabled(False)
        self.lbl_pdf_status.setText("Building PDF document in background...")

        self.pdf_worker = PdfWorker(
            image_paths=filepaths,
            output_pdf_path=save_path,
            page_size_name=page_size,
            orientation=orientation,
            fit_mode=fit_mode,
            margin=margin,
            parent=self
        )
        self.pdf_worker.finished.connect(self._on_pdf_worker_finished)
        self.pdf_worker.start()

    def _on_pdf_worker_finished(self, success: bool, message: str):
        self.btn_export_pdf.setEnabled(True)
        self.lbl_pdf_status.setText("Ready")
        if success:
            QMessageBox.information(self, "PDF Created", "PDF document was created successfully!")
        else:
            QMessageBox.critical(self, "PDF Error", f"Failed to build PDF:\n{message}")

    # ==================== ICON EXPORT ====================
    def select_icon_source_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon Master Image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if file_path:
            self.entry_icon_src.setText(file_path)

    def start_icon_export(self):
        src = self.entry_icon_src.text().strip()
        if not src or not Path(src).exists():
            QMessageBox.warning(self, "No Source", "Please select a valid source image first.")
            return

        chosen_sizes = [sz for sz, chk in self.icon_size_checks.items() if chk.isChecked()]
        if not chosen_sizes:
            QMessageBox.warning(self, "No Sizes", "Please select at least one icon resolution.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Windows Icon", "", "Icon File (*.ico)"
        )
        if not save_path:
            return

        self.lbl_icon_status.setText("Generating icon...")
        ok, msg = generate_ico(src, save_path, sizes=chosen_sizes)
        self.lbl_icon_status.setText("Ready")
        if ok:
            QMessageBox.information(self, "Icon Generated", f"ICO created successfully:\n{save_path}")
        else:
            QMessageBox.critical(self, "Icon Error", f"Failed to generate icon:\n{msg}")

    def closeEvent(self, event: QCloseEvent):
        # Gracefully terminate background workers
        if self.conversion_worker and self.conversion_worker.isRunning():
            self.conversion_worker.request_cancellation()
            self.conversion_worker.wait(1500)
        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.cancel()
            self.preview_worker.wait(500)
        if self.pdf_worker and self.pdf_worker.isRunning():
            self.pdf_worker.cancel()
            self.pdf_worker.wait(500)
        logger.info(f"{APP_NAME} desktop closed gracefully.")
        event.accept()


# Backwards compatibility alias
FormatoApp = MainWindow
