import customtkinter as ctk
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ExifTags
from pathlib import Path
import os
import threading
import concurrent.futures
import tkinter.filedialog as filedialog
from tkinter import messagebox
import json
import time

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    BaseClass = TkinterDnD.Tk
    HAS_DND = True
except ImportError:
    BaseClass = ctk.CTk
    HAS_DND = False

# ==================== CONFIGURATION ====================
LOGO_IMAGE_PATH = "assets/logo.png"
WINDOW_ICON_PATH = "assets/icon.ico"
# ======================================================

# Dark Studio
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FormatoApp(BaseClass):
    def __init__(self):
        super().__init__()
        
        # If BaseClass is TkinterDnD.Tk, we need to explicitly set it up to act like a CTk window
        if HAS_DND and not isinstance(self, ctk.CTk):
            self.configure(bg=ctk.ThemeManager.theme["CTk"]["fg_color"][1])
            
        self.title("Formato - Professional Studio")
        self.geometry("1400x950")
        self.minsize(1150, 750)

        # Window icon
        if os.path.exists(WINDOW_ICON_PATH):
            if WINDOW_ICON_PATH.endswith('.ico'):
                self.iconbitmap(WINDOW_ICON_PATH)
            else:
                icon_img = ctk.CTkImage(Image.open(WINDOW_ICON_PATH), size=(32, 32))
                self.wm_iconphoto(True, icon_img)

        # Basic Variables
        self.output_format = ctk.StringVar(value="JPEG")
        self.quality = ctk.IntVar(value=85)
        self.preserve_exif = ctk.BooleanVar(value=True)
        self.resize_width = ctk.StringVar()
        self.resize_height = ctk.StringVar()
        self.resize_mode = ctk.StringVar(value="Stretch")
        self.output_folder = ctk.StringVar()
        self.selected_files = []
        self.progress_bars = {}

        # Watermark & Renaming Variables
        self.watermark_path = ctk.StringVar(value="")
        self.wm_pos = ctk.StringVar(value="Bottom Right")
        self.wm_size = ctk.DoubleVar(value=0.15)
        self.wm_opacity = ctk.DoubleVar(value=1.0)
        self.wm_margin_x = ctk.StringVar(value="10")
        self.wm_margin_y = ctk.StringVar(value="10")
        
        self.rename_prefix = ctk.StringVar(value="")
        self.rename_suffix = ctk.StringVar(value="")
        
        # Filters
        self.filter_gray = ctk.BooleanVar(value=False)
        self.filter_auto = ctk.BooleanVar(value=False)
        self.filter_sharp = ctk.BooleanVar(value=False)

        # Advanced Adjustments
        self.adj_brightness = ctk.DoubleVar(value=1.0)
        self.adj_contrast = ctk.DoubleVar(value=1.0)
        self.adj_saturation = ctk.DoubleVar(value=1.0)
        self.adj_sharpness = ctk.DoubleVar(value=1.0)

        # Metadata Manager
        self.meta_enable = ctk.BooleanVar(value=False)
        self.meta_author = ctk.StringVar(value="")

        # Smart Compression
        self.smart_compress = ctk.BooleanVar(value=False)
        self.target_kb = ctk.StringVar(value="500")

        # Preview Threading & Memory
        self.preview_thread = None
        self.preview_pending = False
        self.current_preview_file = None
        self.last_preview_time = 0
        self._current_ctk_image = None  # Prevent garbage collection

        self.icon_type = ctk.StringVar(value="Favicon (Web)")
        self.selected_sizes = {
            (16,16): ctk.BooleanVar(value=True), (32,32): ctk.BooleanVar(value=True),
            (48,48): ctk.BooleanVar(value=False), (64,64): ctk.BooleanVar(value=False),
            (128,128): ctk.BooleanVar(value=False), (180,180): ctk.BooleanVar(value=False),
            (192,192): ctk.BooleanVar(value=False), (256,256): ctk.BooleanVar(value=False),
            (512,512): ctk.BooleanVar(value=False),
        }
        self.favicon_source = None
        self.favicon_source_name = ctk.StringVar(value="No image selected")

        self.setup_layout()
        
        # Setup Drag and Drop if supported
        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        files = self.split_dnd_files(event.data)
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp', '.gif'}
        new_files = []
        for f in files:
            if Path(f).suffix.lower() in valid_exts and f not in self.selected_files:
                new_files.append(f)
        
        if new_files:
            self.selected_files.extend(new_files)
            self.update_file_list()
            # Preview first dropped file
            if not self.current_preview_file:
                self.set_preview_image(new_files[0])

    def split_dnd_files(self, data):
        # Handle cross-platform file paths from drag and drop correctly using tk.splitlist
        if hasattr(self, 'tk'):
            return self.tk.splitlist(data)
        if data.startswith('{'):
            return [f.strip('{}') for f in data.split('} {')]
        return data.split()

    def setup_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1E1E1E")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Formato", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        self.btn_batch = ctk.CTkButton(self.sidebar_frame, text="⚡ Batch Process", height=40, anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=lambda: self.select_frame("batch"))
        self.btn_batch.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_pdf = ctk.CTkButton(self.sidebar_frame, text="📄 PDF Export", height=40, anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=lambda: self.select_frame("pdf"))
        self.btn_pdf.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.btn_icon = ctk.CTkButton(self.sidebar_frame, text="🎨 Icon Generator", height=40, anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), command=lambda: self.select_frame("icon"))
        self.btn_icon.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Ready", font=ctk.CTkFont(size=12), text_color="gray60")
        self.status_label.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="s")

        # --- Main Content Frames ---
        self.frames = {}
        
        self.frames["batch"] = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["pdf"] = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["icon"] = ctk.CTkFrame(self, fg_color="transparent")

        for frame in self.frames.values():
            frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.setup_batch_view()
        self.setup_pdf_view()
        self.setup_icon_view()

        self.select_frame("batch")

    def select_frame(self, frame_name):
        buttons = {"batch": self.btn_batch, "pdf": self.btn_pdf, "icon": self.btn_icon}
        for name, btn in buttons.items():
            if name == frame_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

        self.frames[frame_name].tkraise()

    def create_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="#2B2B2B", corner_radius=10)
        card.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))
        return content

    def setup_batch_view(self):
        frame = self.frames["batch"]
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=6)
        frame.grid_columnconfigure(1, weight=4)

        # Left Panel: File List & Preview
        left_panel = ctk.CTkFrame(frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=1) # File list
        left_panel.grid_rowconfigure(3, weight=1) # Preview

        # --- Queue Section ---
        queue_frame = ctk.CTkFrame(left_panel, fg_color="#2B2B2B", corner_radius=10)
        queue_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", pady=(0, 10))
        queue_frame.grid_rowconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(queue_frame, text="Queue (Drag & Drop Supported)", font=ctk.CTkFont(size=18, weight="bold"))
        title_lbl.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.file_listbox = ctk.CTkScrollableFrame(queue_frame, fg_color="transparent")
        self.file_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        btns = ctk.CTkFrame(queue_frame, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        btns.grid_columnconfigure((0,1), weight=1)

        ctk.CTkButton(btns, text="➕ Add Files", height=35, command=self.add_files).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(btns, text="🗑 Clear", height=35, fg_color="#5C3A3A", hover_color="#7A4C4C", command=self.clear_files).pack(side="right", padx=5, fill="x", expand=True)

        self.progress = ctk.CTkProgressBar(queue_frame, height=8)
        self.progress.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)

        # --- Preview Section ---
        preview_frame = ctk.CTkFrame(left_panel, fg_color="#2B2B2B", corner_radius=10)
        preview_frame.grid(row=2, column=0, rowspan=2, sticky="nsew")
        preview_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(preview_frame, text="Live Preview", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))
        self.preview_label = ctk.CTkLabel(preview_frame, text="Select a file to preview")
        self.preview_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Right Panel: Settings (Scrollable)
        right_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        right_scroll.grid(row=0, column=1, sticky="nsew")

        # Card 1: Output Settings & Smart Compress
        card_out = self.create_card(right_scroll, "Output Format")
        ctk.CTkComboBox(card_out, values=["JPEG", "PNG", "WEBP", "TIFF", "BMP"], variable=self.output_format).pack(fill="x", pady=5)
        
        qual_frame = ctk.CTkFrame(card_out, fg_color="transparent")
        qual_frame.pack(fill="x", pady=(5,0))
        ctk.CTkLabel(qual_frame, text="Quality").pack(side="left")
        ctk.CTkSlider(card_out, from_=1, to=100, variable=self.quality, number_of_steps=99).pack(fill="x", pady=5)

        smart_frame = ctk.CTkFrame(card_out, fg_color="transparent")
        smart_frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(smart_frame, text="Smart Compression", variable=self.smart_compress).pack(side="left")
        ctk.CTkEntry(smart_frame, textvariable=self.target_kb, width=60, placeholder_text="KB").pack(side="right")
        ctk.CTkLabel(smart_frame, text="Target KB:").pack(side="right", padx=5)

        # Card 2: Resize
        card_res = self.create_card(right_scroll, "Smart Resize (Leave one empty to keep aspect ratio)")
        res_row = ctk.CTkFrame(card_res, fg_color="transparent")
        res_row.pack(fill="x")
        
        w_entry = ctk.CTkEntry(res_row, placeholder_text="Width", textvariable=self.resize_width, width=60)
        w_entry.pack(side="left", padx=(0, 5))
        w_entry.bind("<KeyRelease>", lambda e: self.trigger_preview_update())
        
        ctk.CTkLabel(res_row, text="×").pack(side="left")
        
        h_entry = ctk.CTkEntry(res_row, placeholder_text="Height", textvariable=self.resize_height, width=60)
        h_entry.pack(side="left", padx=(5, 10))
        h_entry.bind("<KeyRelease>", lambda e: self.trigger_preview_update())
        
        opt_mode = ctk.CTkOptionMenu(res_row, values=["Stretch", "Fit (Maintain AR)", "Fill/Crop"], variable=self.resize_mode, width=120, command=lambda _: self.trigger_preview_update())
        opt_mode.pack(side="right", fill="x", expand=True)

        # Card 3: Advanced Adjustments
        card_adj = self.create_card(right_scroll, "Advanced Adjustments")
        self._add_slider_row(card_adj, "Brightness", self.adj_brightness, 0.2, 3.0)
        self._add_slider_row(card_adj, "Contrast", self.adj_contrast, 0.2, 3.0)
        self._add_slider_row(card_adj, "Saturation", self.adj_saturation, 0.2, 3.0)
        self._add_slider_row(card_adj, "Sharpness", self.adj_sharpness, 0.2, 5.0)

        # Card 4: Enhancements
        card_enh = self.create_card(right_scroll, "Enhancements & Filters")
        ctk.CTkCheckBox(card_enh, text="Grayscale", variable=self.filter_gray, command=self.trigger_preview_update).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(card_enh, text="Auto-Contrast", variable=self.filter_auto, command=self.trigger_preview_update).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(card_enh, text="Sharpen", variable=self.filter_sharp, command=self.trigger_preview_update).pack(side="left")

        # Card 5: Metadata
        card_meta = self.create_card(right_scroll, "Metadata Manager")
        ctk.CTkCheckBox(card_meta, text="Preserve Original EXIF", variable=self.preserve_exif).pack(anchor="w", pady=(0, 5))
        ctk.CTkCheckBox(card_meta, text="Write Custom Metadata", variable=self.meta_enable).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(card_meta, textvariable=self.meta_author, placeholder_text="Author Name").pack(fill="x")

        # Card 6: Watermark & Rename
        card_wm = self.create_card(right_scroll, "Watermark & Renaming")
        
        # Watermark Path
        wm_f = ctk.CTkFrame(card_wm, fg_color="transparent")
        wm_f.pack(fill="x", pady=(0, 5))
        ctk.CTkEntry(wm_f, textvariable=self.watermark_path, state="readonly", placeholder_text="Watermark (PNG)").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(wm_f, text="📁", width=40, command=self.select_watermark).pack(side="right")
        
        # Watermark Advanced Settings
        wm_adv1 = ctk.CTkFrame(card_wm, fg_color="transparent")
        wm_adv1.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(wm_adv1, text="Pos:").pack(side="left")
        ctk.CTkOptionMenu(wm_adv1, values=["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"], variable=self.wm_pos, width=110, command=lambda _: self.trigger_preview_update()).pack(side="left", padx=5)
        
        ctk.CTkLabel(wm_adv1, text="Size:").pack(side="left", padx=(5,0))
        ctk.CTkSlider(wm_adv1, from_=0.05, to=0.50, variable=self.wm_size, width=80, command=lambda _: self.trigger_preview_update()).pack(side="left", padx=5)
        
        wm_adv2 = ctk.CTkFrame(card_wm, fg_color="transparent")
        wm_adv2.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(wm_adv2, text="Opacity:").pack(side="left")
        ctk.CTkSlider(wm_adv2, from_=0.0, to=1.0, variable=self.wm_opacity, width=80, command=lambda _: self.trigger_preview_update()).pack(side="left", padx=5)
        
        ctk.CTkLabel(wm_adv2, text="Margins (X,Y):").pack(side="left", padx=(5,0))
        mx = ctk.CTkEntry(wm_adv2, textvariable=self.wm_margin_x, width=35)
        mx.pack(side="left", padx=2)
        mx.bind("<KeyRelease>", lambda e: self.trigger_preview_update())
        my = ctk.CTkEntry(wm_adv2, textvariable=self.wm_margin_y, width=35)
        my.pack(side="left", padx=2)
        my.bind("<KeyRelease>", lambda e: self.trigger_preview_update())

        rn_f = ctk.CTkFrame(card_wm, fg_color="transparent")
        rn_f.pack(fill="x")
        ctk.CTkEntry(rn_f, placeholder_text="Prefix", textvariable=self.rename_prefix).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkEntry(rn_f, placeholder_text="Suffix", textvariable=self.rename_suffix).pack(side="right", fill="x", expand=True)

        # Card 7: Destination & Start
        card_dest = self.create_card(right_scroll, "Destination Folder")
        dest_f = ctk.CTkFrame(card_dest, fg_color="transparent")
        dest_f.pack(fill="x", pady=(0, 15))
        ctk.CTkEntry(dest_f, textvariable=self.output_folder, placeholder_text="Required", state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(dest_f, text="📁", width=40, command=self.choose_output_folder).pack(side="right")

        self.convert_btn = ctk.CTkButton(card_dest, text="🚀 START PROCESSING", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_conversion)
        self.convert_btn.pack(fill="x")

        # Presets Panel
        preset_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        preset_frame.pack(fill="x", pady=10)
        ctk.CTkButton(preset_frame, text="💾 Save Preset", command=self.save_preset).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(preset_frame, text="📂 Load Preset", command=self.load_preset).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _add_slider_row(self, parent, label, variable, min_val, max_val):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=label, width=80, anchor="w").pack(side="left")
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, variable=variable, command=lambda _: self.trigger_preview_update())
        slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # Double click label to reset
        def reset(e):
            variable.set(1.0)
            self.trigger_preview_update()
        lbl_val = ctk.CTkLabel(frame, text="1.0", width=30)
        lbl_val.pack(side="right")
        lbl_val.bind("<Double-Button-1>", reset)
        
        def update_lbl(*args):
            lbl_val.configure(text=f"{variable.get():.1f}")
        variable.trace_add("write", update_lbl)
        update_lbl()

    def setup_pdf_view(self):
        frame = self.frames["pdf"]
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        container = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=15)
        container.grid(row=0, column=0, pady=50, padx=50, sticky="nsew")
        
        ctk.CTkLabel(container, text="📄 PDF Builder", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(60, 10))
        ctk.CTkLabel(container, text="Combine all files in your 'Queue' into a single PDF document.", text_color="gray60").pack(pady=10)
        
        ctk.CTkButton(container, text="Export to PDF", height=50, width=200, font=ctk.CTkFont(size=16, weight="bold"), command=self.export_pdf).pack(pady=40)

    def setup_icon_view(self):
        frame = self.frames["icon"]
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=15)
        container.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")

        ctk.CTkLabel(container, text="🎨 Icon & Favicon Generator", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(30, 20))

        src_f = ctk.CTkFrame(container, fg_color="transparent")
        src_f.pack(fill="x", padx=40, pady=10)
        self.favicon_source_entry = ctk.CTkEntry(src_f, textvariable=self.favicon_source_name, state="readonly", width=300)
        self.favicon_source_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(src_f, text="📁 Select Source", command=self.select_favicon_source).pack(side="right")

        type_f = ctk.CTkFrame(container, fg_color="transparent")
        type_f.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(type_f, text="Target Type:").pack(side="left", padx=(0, 10))
        ctk.CTkOptionMenu(type_f, values=["Favicon (Web)", "Icon (App)"], variable=self.icon_type, command=self.update_default_sizes).pack(side="left")

        sizes_frame = ctk.CTkFrame(container, fg_color="#1E1E1E", corner_radius=10)
        sizes_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        size_labels = {
            (16,16): "16×16", (32,32): "32×32",
            (48,48): "48×48", (64,64): "64×64", (128,128): "128×128",
            (180,180): "180×180", (192,192): "192×192",
            (256,256): "256×256", (512,512): "512×512",
        }
        
        row, col = 0, 0
        for size, var in self.selected_sizes.items():
            ctk.CTkCheckBox(sizes_frame, text=size_labels[size], variable=var).grid(row=row, column=col, padx=20, pady=15, sticky="w")
            col += 1
            if col > 2:
                col = 0
                row += 1

        ctk.CTkButton(container, text="⚡ Generate Icons", height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.generate_icon).pack(pady=30, padx=40, fill="x")

    # =========================================================================
    # Preset System
    # =========================================================================
    def save_preset(self):
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file: return
        
        data = {
            "output_format": self.output_format.get(),
            "quality": self.quality.get(),
            "smart_compress": self.smart_compress.get(),
            "target_kb": self.target_kb.get(),
            "resize_width": self.resize_width.get(),
            "resize_height": self.resize_height.get(),
            "resize_mode": self.resize_mode.get(),
            "filter_gray": self.filter_gray.get(),
            "filter_auto": self.filter_auto.get(),
            "filter_sharp": self.filter_sharp.get(),
            "preserve_exif": self.preserve_exif.get(),
            "meta_enable": self.meta_enable.get(),
            "meta_author": self.meta_author.get(),
            "adj_brightness": self.adj_brightness.get(),
            "adj_contrast": self.adj_contrast.get(),
            "adj_saturation": self.adj_saturation.get(),
            "adj_sharpness": self.adj_sharpness.get(),
            "wm_pos": self.wm_pos.get(),
            "wm_size": self.wm_size.get(),
            "wm_opacity": self.wm_opacity.get(),
            "wm_margin_x": self.wm_margin_x.get(),
            "wm_margin_y": self.wm_margin_y.get()
        }
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Success", "Preset saved successfully!")

    def load_preset(self):
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file: return
        
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            self.output_format.set(data.get("output_format", "JPEG"))
            self.quality.set(data.get("quality", 85))
            self.smart_compress.set(data.get("smart_compress", False))
            self.target_kb.set(data.get("target_kb", "500"))
            self.resize_width.set(data.get("resize_width", ""))
            self.resize_height.set(data.get("resize_height", ""))
            self.resize_mode.set(data.get("resize_mode", "Stretch"))
            self.filter_gray.set(data.get("filter_gray", False))
            self.filter_auto.set(data.get("filter_auto", False))
            self.filter_sharp.set(data.get("filter_sharp", False))
            self.preserve_exif.set(data.get("preserve_exif", True))
            self.meta_enable.set(data.get("meta_enable", False))
            self.meta_author.set(data.get("meta_author", ""))
            self.adj_brightness.set(data.get("adj_brightness", 1.0))
            self.adj_contrast.set(data.get("adj_contrast", 1.0))
            self.adj_saturation.set(data.get("adj_saturation", 1.0))
            self.adj_sharpness.set(data.get("adj_sharpness", 1.0))
            self.wm_pos.set(data.get("wm_pos", "Bottom Right"))
            self.wm_size.set(data.get("wm_size", 0.15))
            self.wm_opacity.set(data.get("wm_opacity", 1.0))
            self.wm_margin_x.set(data.get("wm_margin_x", "10"))
            self.wm_margin_y.set(data.get("wm_margin_y", "10"))
            self.trigger_preview_update()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load preset: {e}")

    # =========================================================================
    # Live Preview System
    # =========================================================================
    def set_preview_image(self, filepath):
        self.current_preview_file = filepath
        self.trigger_preview_update()

    def trigger_preview_update(self):
        if not self.current_preview_file: return
        self.last_preview_time = time.time()
        if not self.preview_pending:
            self.preview_pending = True
            self.after(250, self._process_preview_debounce)

    def _process_preview_debounce(self):
        if time.time() - self.last_preview_time < 0.2:
            self.after(100, self._process_preview_debounce)
            return
            
        self.preview_pending = False
        params = self._get_current_params()
        
        # Calculate resize dimensions for preview
        try:
            w_str, h_str = self.resize_width.get().strip(), self.resize_height.get().strip()
            # We don't apply the actual resize dimensions to the preview to save memory, 
            # but we use the ratio if needed. We will just use thumbnail logic to simulate it.
            params["resize"] = get_resize_dimensions((1000, 1000), w_str, h_str) # dummy check for validity
        except:
            params["resize"] = None

        def task():
            try:
                im = Image.open(self.current_preview_file)
                
                # We need to maintain aspect ratio for preview and keep it small
                preview_size = (400, 400)
                
                # Simulated Resize impact
                try:
                    w_str, h_str = self.resize_width.get().strip(), self.resize_height.get().strip()
                    res_dim = get_resize_dimensions(im.size, w_str, h_str)
                    if res_dim:
                        if params["mode"] == "Fit (Maintain AR)": im = ImageOps.contain(im, res_dim, Image.LANCZOS)
                        elif params["mode"] == "Fill/Crop": im = ImageOps.fit(im, res_dim, Image.LANCZOS)
                        else: im = im.resize(res_dim, Image.LANCZOS)
                except: pass

                im.thumbnail(preview_size, Image.LANCZOS)
                
                # Filters
                if params["f_gray"]: im = im.convert("L")
                if params["f_auto"]:
                    try: im = ImageOps.autocontrast(im.convert("RGB"))
                    except: pass
                if params["f_sharp"]: im = im.filter(ImageFilter.SHARPEN)

                if params["adj_b"] != 1.0: im = ImageEnhance.Brightness(im).enhance(params["adj_b"])
                if params["adj_c"] != 1.0: im = ImageEnhance.Contrast(im).enhance(params["adj_c"])
                if params["adj_s"] != 1.0: im = ImageEnhance.Color(im).enhance(params["adj_s"])
                if params["adj_sh"] != 1.0: im = ImageEnhance.Sharpness(im).enhance(params["adj_sh"])
                
                # Watermark
                im = apply_watermark(im, params)
                
                self._current_ctk_image = ctk.CTkImage(im, size=im.size)
                self.after(0, lambda: self.preview_label.configure(image=self._current_ctk_image, text=""))
            except Exception as e:
                pass
                
        if self.preview_thread and self.preview_thread.is_alive():
            pass # Let it finish
        self.preview_thread = threading.Thread(target=task, daemon=True)
        self.preview_thread.start()

    # =========================================================================
    # Other Functions
    # =========================================================================
    def update_default_sizes(self, choice):
        defaults = {
            "Favicon (Web)": [(16,16), (32,32), (180,180), (192,192), (256,256), (512,512)],
            "Icon (App)": [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256), (512,512)]
        }
        selected = defaults.get(choice, [(16,16), (32,32)])
        for size, var in self.selected_sizes.items():
            var.set(size in selected)

    def select_watermark(self):
        file = filedialog.askopenfilename(title="Select Logo (PNG)", filetypes=[("PNG Files", "*.png")])
        if file:
            self.watermark_path.set(file)
            self.trigger_preview_update()

    def select_favicon_source(self):
        file = filedialog.askopenfilename(title="Select Source Image", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if file:
            self.favicon_source = file
            self.favicon_source_name.set(Path(file).name)

    def generate_icon(self):
        if not self.favicon_source or not os.path.exists(self.favicon_source):
            messagebox.showwarning("Warning", "Please select a valid source image!")
            return

        selected_sizes = [s for s, v in self.selected_sizes.items() if v.get()]
        if not selected_sizes:
            messagebox.showwarning("Warning", "Please select at least one size!")
            return

        base_name = "favicon" if self.icon_type.get() == "Favicon (Web)" else "app-icon"
        save_folder = filedialog.askdirectory(title="Select Save Folder")
        if not save_folder: return

        save_folder = Path(save_folder)
        self.status_label.configure(text="Generating Icons...", text_color="orange")

        def task():
            try:
                with Image.open(self.favicon_source) as img:
                    base_img = img.convert("RGBA")
                    ico_images, ico_sizes, files = [], [], [f"{base_name}.ico"]

                    for size in selected_sizes:
                        resized = base_img.resize(size, Image.LANCZOS)
                        resized.save(save_folder / f"{base_name}-{size[0]}x{size[1]}.png", "PNG")
                        files.append(f"{base_name}-{size[0]}x{size[1]}.png")
                        ico_images.append(resized.convert("RGB") if size[0] <= 48 else resized)
                        ico_sizes.append(size)

                    if ico_images:
                        ico_images[0].save(save_folder / f"{base_name}.ico", format='ICO', append_images=ico_images[1:], sizes=ico_sizes)

                self.after(0, lambda: self.status_label.configure(text="Icon generation complete!", text_color="green"))
                self.after(0, lambda: messagebox.showinfo("Success", "Icons generated successfully!"))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text="Error!", text_color="red"))
                self.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=task, daemon=True).start()

    def add_files(self):
        files = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.tiff *.bmp *.gif")])
        if files:
            new = [f for f in files if f not in self.selected_files]
            self.selected_files.extend(new)
            self.update_file_list()
            if new and not self.current_preview_file:
                self.set_preview_image(new[0])

    def clear_files(self):
        self.selected_files.clear()
        self.progress_bars.clear()
        self.current_preview_file = None
        self._current_ctk_image = None
        self.preview_label.configure(image="", text="Select a file to preview")
        for w in self.file_listbox.winfo_children():
            w.destroy()

    def update_file_list(self):
        for w in self.file_listbox.winfo_children():
            w.destroy()
        self.progress_bars.clear()

        for fp in self.selected_files:
            p = Path(fp)
            frame = ctk.CTkFrame(self.file_listbox, fg_color="#1E1E1E")
            frame.pack(fill="x", pady=2, padx=2)

            # Make row clickable for preview
            lbl = ctk.CTkLabel(frame, text=p.name, anchor="w", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="left", padx=10, pady=5)
            lbl.bind("<Button-1>", lambda e, f=fp: self.set_preview_image(f))
            frame.bind("<Button-1>", lambda e, f=fp: self.set_preview_image(f))

            pb = ctk.CTkProgressBar(frame, width=80, height=8)
            pb.pack(side="right", padx=10)
            pb.set(0)
            self.progress_bars[fp] = pb

    def choose_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def _get_current_params(self):
        return {
            "fmt": self.output_format.get(),
            "qual": self.quality.get(),
            "exif": self.preserve_exif.get(),
            "out_dir": Path(self.output_folder.get()) if self.output_folder.get() else None,
            "mode": self.resize_mode.get(),
            "wm": self.watermark_path.get(),
            "wm_pos": self.wm_pos.get(),
            "wm_size": self.wm_size.get(),
            "wm_opacity": self.wm_opacity.get(),
            "wm_margin_x": int(self.wm_margin_x.get()) if self.wm_margin_x.get().isdigit() else 10,
            "wm_margin_y": int(self.wm_margin_y.get()) if self.wm_margin_y.get().isdigit() else 10,
            "pref": self.rename_prefix.get().strip(),
            "suff": self.rename_suffix.get().strip(),
            "f_gray": self.filter_gray.get(),
            "f_auto": self.filter_auto.get(),
            "f_sharp": self.filter_sharp.get(),
            "adj_b": self.adj_brightness.get(),
            "adj_c": self.adj_contrast.get(),
            "adj_s": self.adj_saturation.get(),
            "adj_sh": self.adj_sharpness.get(),
            "smart": self.smart_compress.get(),
            "target_kb": int(self.target_kb.get()) if self.target_kb.get().isdigit() else 500,
            "meta_en": self.meta_enable.get(),
            "meta_auth": self.meta_author.get()
        }

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected!")
            return
        if not self.output_folder.get():
            messagebox.showwarning("Warning", "Please select an output folder!")
            return

        self.convert_btn.configure(state="disabled", text="⚙️ Processing...")
        self.status_label.configure(text="Processing...", text_color="orange")
        self.progress.set(0)
        
        params = self._get_current_params()

        # Validate resize
        try:
            w_str, h_str = self.resize_width.get().strip(), self.resize_height.get().strip()
            # We delay calculating actual dimensions to convert_image because aspect ratio depends on each image
            params["res_w_str"] = w_str
            params["res_h_str"] = h_str
        except Exception as e:
            messagebox.showerror("Error", "Invalid resize dimensions!")
            self.reset_conversion_ui()
            return

        threading.Thread(target=self.convert_all, args=(params,), daemon=True).start()

    def convert_all(self, p):
        total = len(self.selected_files)
        done = 0
        
        def process_single(idx, fp):
            in_p = Path(fp)
            ext = "jpg" if p["fmt"] == "JPEG" else p["fmt"].lower()
            
            new_name = in_p.stem
            if p["pref"] or p["suff"]:
                new_name = f"{p['pref']}_{idx:03d}_{p['suff']}".strip("_")
                
            out_p = p["out_dir"] / f"{new_name}.{ext}"
            
            res = convert_image(
                input_path=str(in_p), output_path=str(out_p), p=p
            )
            return fp, res

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_single, i+1, fp) for i, fp in enumerate(self.selected_files)]
            
            for future in concurrent.futures.as_completed(futures):
                fp, res = future.result()
                self.after(0, lambda f=fp, r=res: self.update_single_progress(f, r))
                done += 1
                self.after(0, lambda d=done: self.progress.set(d / total))

        self.after(0, self.finish_conversion)

    def export_pdf(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected in Queue!")
            return
            
        save_path = filedialog.asksaveasfilename(title="Save PDF", defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not save_path:
            return
            
        self.status_label.configure(text="Generating PDF...", text_color="orange")
        
        def task():
            try:
                images = []
                for fp in self.selected_files:
                    img = Image.open(fp)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img)
                    
                if images:
                    images[0].save(save_path, save_all=True, append_images=images[1:])
                    
                self.after(0, lambda: self.status_label.configure(text="Ready", text_color="gray60"))
                self.after(0, lambda: messagebox.showinfo("Success", "PDF created successfully!"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self.status_label.configure(text="Ready", text_color="gray60"))
                
        threading.Thread(target=task, daemon=True).start()

    def update_single_progress(self, fp, res):
        if fp in self.progress_bars:
            pb = self.progress_bars[fp]
            pb.set(1.0)
            pb.configure(progress_color="#28a745" if res["success"] else "#dc3545")

    def finish_conversion(self):
        self.convert_btn.configure(state="normal", text="🚀 START PROCESSING")
        self.status_label.configure(text="Finished!", text_color="green")
        messagebox.showinfo("Success", "All tasks finished!")

    def reset_conversion_ui(self):
        self.convert_btn.configure(state="normal", text="🚀 START PROCESSING")
        self.status_label.configure(text="Ready", text_color="gray60")

def get_resize_dimensions(im_size, w_str, h_str):
    w = int(w_str) if w_str and w_str.isdigit() else None
    h = int(h_str) if h_str and h_str.isdigit() else None
    orig_w, orig_h = im_size
    
    if w and not h:
        h = int(orig_h * (w / float(orig_w)))
    elif h and not w:
        w = int(orig_w * (h / float(orig_h)))
        
    return (w, h) if w and h else None

def apply_watermark(im, p):
    if p.get("wm") and os.path.exists(p["wm"]):
        with Image.open(p["wm"]).convert("RGBA") as wm:
            # Calculate size
            target_w = int(im.size[0] * p["wm_size"])
            if target_w <= 0: return im
            
            ratio = target_w / float(wm.size[0])
            target_h = int(float(wm.size[1]) * ratio)
            if target_h <= 0: return im
            
            wm = wm.resize((target_w, target_h), Image.LANCZOS)
            
            # Opacity
            if p["wm_opacity"] < 1.0:
                alpha = wm.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(p["wm_opacity"])
                wm.putalpha(alpha)
            
            # Margins
            mx = p["wm_margin_x"]
            my = p["wm_margin_y"]
            
            # Position
            pos_str = p["wm_pos"]
            if pos_str == "Top Left":
                x, y = mx, my
            elif pos_str == "Top Right":
                x, y = im.size[0] - wm.size[0] - mx, my
            elif pos_str == "Bottom Left":
                x, y = mx, im.size[1] - wm.size[1] - my
            elif pos_str == "Center":
                x, y = (im.size[0] - wm.size[0]) // 2, (im.size[1] - wm.size[1]) // 2
            else: # Bottom Right
                x, y = im.size[0] - wm.size[0] - mx, im.size[1] - wm.size[1] - my
            
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            layer = Image.new("RGBA", im.size, (0,0,0,0))
            layer.paste(wm, (x, y))
            im = Image.alpha_composite(im, layer)
            
            if p["fmt"].upper() in ("JPEG", "JPG"):
                im = im.convert("RGB")
    return im

def convert_image(input_path, output_path, p):
    try:
        with Image.open(input_path) as im:
            # 1. Base Filters
            if p["f_gray"]: im = im.convert("L")
            if p["f_auto"]:
                try: im = ImageOps.autocontrast(im.convert("RGB"))
                except: pass
            if p["f_sharp"]: im = im.filter(ImageFilter.SHARPEN)

            # 2. Advanced Adjustments
            if p["adj_b"] != 1.0: im = ImageEnhance.Brightness(im).enhance(p["adj_b"])
            if p["adj_c"] != 1.0: im = ImageEnhance.Contrast(im).enhance(p["adj_c"])
            if p["adj_s"] != 1.0: im = ImageEnhance.Color(im).enhance(p["adj_s"])
            if p["adj_sh"] != 1.0: im = ImageEnhance.Sharpness(im).enhance(p["adj_sh"])

            # 3. Resize Logic
            res_dim = get_resize_dimensions(im.size, p.get("res_w_str", ""), p.get("res_h_str", ""))
            if res_dim:
                if p["mode"] == "Fit (Maintain AR)": im = ImageOps.contain(im, res_dim, Image.LANCZOS)
                elif p["mode"] == "Fill/Crop": im = ImageOps.fit(im, res_dim, Image.LANCZOS)
                else: im = im.resize(res_dim, Image.LANCZOS)

            kwargs = {}
            exif = im.info.get("exif") if p["exif"] and "exif" in im.info else None
            
            # Custom Metadata implementation (Basic implementation for JPG/TIFF)
            if p["meta_en"] and p["meta_auth"] and p["fmt"].upper() in ("JPEG", "JPG", "TIFF"):
                if not exif:
                    exif = Image.Exif()
                else:
                    exif = im.getexif()
                # 315 is standard Artist/Author tag in EXIF
                exif[315] = p["meta_auth"]
                kwargs["exif"] = exif.tobytes()
            elif exif and p["fmt"].upper() in ("JPEG", "JPG"):
                kwargs["exif"] = exif

            # Ensure Correct Modes
            if p["fmt"].upper() in ("JPEG", "JPG") and im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P": im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if 'A' in im.getbands() else None)
                im = bg

            # 4. Watermark System
            im = apply_watermark(im, p)

            # Output Formatting
            if p["fmt"].upper() in ("JPEG", "WEBP"):
                kwargs["quality"] = p["qual"]
                kwargs["optimize"] = True
            if p["fmt"].upper() == "PNG": kwargs["compress_level"] = 6

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Smart Compression Binary Search
            if p["smart"] and p["fmt"].upper() in ("JPEG", "JPG", "WEBP"):
                low, high = 10, 100
                best_quality = p["qual"]
                target_bytes = p["target_kb"] * 1024
                
                for _ in range(7):  # Max 7 steps for binary search
                    mid = (low + high) // 2
                    kwargs["quality"] = mid
                    im.save(output_path, p["fmt"], **kwargs)
                    size = os.path.getsize(output_path)
                    
                    if size <= target_bytes:
                        best_quality = mid
                        low = mid + 1
                    else:
                        high = mid - 1
                
                kwargs["quality"] = best_quality
                im.save(output_path, p["fmt"], **kwargs)
            else:
                im.save(output_path, p["fmt"], **kwargs)

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    app = FormatoApp()
    app.mainloop()
