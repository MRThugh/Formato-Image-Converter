import customtkinter as ctk
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pathlib import Path
import os
import threading
import concurrent.futures
import tkinter.filedialog as filedialog
from tkinter import messagebox

# ==================== CONFIGURATION ====================
LOGO_IMAGE_PATH = "assets/logo.png"
WINDOW_ICON_PATH = "assets/icon.ico"
# ======================================================

# Dark Studio
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FormatoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Formato - Professional Studio")
        self.geometry("1200x800")
        self.minsize(1050, 650)

        # Window icon
        if os.path.exists(WINDOW_ICON_PATH):
            if WINDOW_ICON_PATH.endswith('.ico'):
                self.iconbitmap(WINDOW_ICON_PATH)
            else:
                icon_img = ctk.CTkImage(Image.open(WINDOW_ICON_PATH), size=(32, 32))
                self.wm_iconphoto(True, icon_img)

        # Variables
        self.output_format = ctk.StringVar(value="JPEG")
        self.quality = ctk.IntVar(value=85)
        self.preserve_exif = ctk.BooleanVar(value=True)
        self.resize_width = ctk.StringVar()
        self.resize_height = ctk.StringVar()
        self.resize_mode = ctk.StringVar(value="Stretch")
        self.output_folder = ctk.StringVar()
        self.selected_files = []
        self.progress_bars = {}

        self.watermark_path = ctk.StringVar(value="")
        self.rename_prefix = ctk.StringVar(value="")
        self.rename_suffix = ctk.StringVar(value="")
        self.filter_gray = ctk.BooleanVar(value=False)
        self.filter_auto = ctk.BooleanVar(value=False)
        self.filter_sharp = ctk.BooleanVar(value=False)

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

    def setup_layout(self):
        # Grid Configuration: Sidebar (col 0), Main Content (col 1)
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

        # Start with Batch frame
        self.select_frame("batch")

    def select_frame(self, frame_name):
        # Update button colors to indicate active tab
        buttons = {"batch": self.btn_batch, "pdf": self.btn_pdf, "icon": self.btn_icon}
        for name, btn in buttons.items():
            if name == frame_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

        # Bring selected frame to front
        self.frames[frame_name].tkraise()

    def create_card(self, parent, title):
        """Helper to create visually distinct cards for settings"""
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

        # Left Panel: File List
        left_panel = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=10)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left_panel, text="Queue", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.file_listbox = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.file_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        btns = ctk.CTkFrame(left_panel, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        btns.grid_columnconfigure((0,1), weight=1)

        ctk.CTkButton(btns, text="➕ Add Files", height=35, command=self.add_files).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(btns, text="🗑 Clear", height=35, fg_color="#5C3A3A", hover_color="#7A4C4C", command=self.clear_files).pack(side="right", padx=5, fill="x", expand=True)

        self.progress = ctk.CTkProgressBar(left_panel, height=8)
        self.progress.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)

        # Right Panel: Settings (Scrollable)
        right_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        right_scroll.grid(row=0, column=1, sticky="nsew")

        # Card 1: Output Settings
        card_out = self.create_card(right_scroll, "Output Format")
        ctk.CTkComboBox(card_out, values=["JPEG", "PNG", "WEBP", "TIFF", "BMP"], variable=self.output_format).pack(fill="x", pady=5)
        ctk.CTkLabel(card_out, text="Quality").pack(anchor="w", pady=(5,0))
        ctk.CTkSlider(card_out, from_=1, to=100, variable=self.quality, number_of_steps=99).pack(fill="x")

        # Card 2: Resize
        card_res = self.create_card(right_scroll, "Smart Resize")
        res_row = ctk.CTkFrame(card_res, fg_color="transparent")
        res_row.pack(fill="x")
        ctk.CTkEntry(res_row, placeholder_text="Width", textvariable=self.resize_width, width=60).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(res_row, text="×").pack(side="left")
        ctk.CTkEntry(res_row, placeholder_text="Height", textvariable=self.resize_height, width=60).pack(side="left", padx=(5, 10))
        ctk.CTkOptionMenu(res_row, values=["Stretch", "Fit (Maintain AR)", "Fill/Crop"], variable=self.resize_mode, width=120).pack(side="right", fill="x", expand=True)

        # Card 3: Enhancements
        card_enh = self.create_card(right_scroll, "Enhancements & Filters")
        ctk.CTkCheckBox(card_enh, text="Grayscale", variable=self.filter_gray).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(card_enh, text="Auto-Contrast", variable=self.filter_auto).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(card_enh, text="Sharpen", variable=self.filter_sharp).pack(side="left")

        # Card 4: Watermark & Rename
        card_wm = self.create_card(right_scroll, "Watermark & Renaming")
        wm_f = ctk.CTkFrame(card_wm, fg_color="transparent")
        wm_f.pack(fill="x", pady=(0, 10))
        ctk.CTkEntry(wm_f, textvariable=self.watermark_path, state="readonly", placeholder_text="Watermark (PNG)").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(wm_f, text="📁", width=40, command=self.select_watermark).pack(side="right")
        
        rn_f = ctk.CTkFrame(card_wm, fg_color="transparent")
        rn_f.pack(fill="x")
        ctk.CTkEntry(rn_f, placeholder_text="Prefix", textvariable=self.rename_prefix).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkEntry(rn_f, placeholder_text="Suffix", textvariable=self.rename_suffix).pack(side="right", fill="x", expand=True)

        # Card 5: Destination & Start
        card_dest = self.create_card(right_scroll, "Destination Folder")
        dest_f = ctk.CTkFrame(card_dest, fg_color="transparent")
        dest_f.pack(fill="x", pady=(0, 15))
        ctk.CTkEntry(dest_f, textvariable=self.output_folder, placeholder_text="Required", state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(dest_f, text="📁", width=40, command=self.choose_output_folder).pack(side="right")

        self.convert_btn = ctk.CTkButton(card_dest, text="🚀 START PROCESSING", height=45, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_conversion)
        self.convert_btn.pack(fill="x")

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
        
        # Grid layout for checkboxes
        row, col = 0, 0
        for size, var in self.selected_sizes.items():
            ctk.CTkCheckBox(sizes_frame, text=size_labels[size], variable=var).grid(row=row, column=col, padx=20, pady=15, sticky="w")
            col += 1
            if col > 2:
                col = 0
                row += 1

        ctk.CTkButton(container, text="⚡ Generate Icons", height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.generate_icon).pack(pady=30, padx=40, fill="x")

    # =========================================================================
    # Other                     Functions
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
        if not save_folder:
            return

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

    def clear_files(self):
        self.selected_files.clear()
        self.progress_bars.clear()
        for w in self.file_listbox.winfo_children():
            w.destroy()

    def update_file_list(self):
        for w in self.file_listbox.winfo_children():
            w.destroy()
        self.progress_bars.clear()

        for fp in self.selected_files:
            p = Path(fp)
            size_mb = round(p.stat().st_size / (1024**2), 2)
            frame = ctk.CTkFrame(self.file_listbox, fg_color="#1E1E1E")
            frame.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(frame, text=p.name, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            pb = ctk.CTkProgressBar(frame, width=80, height=8)
            pb.pack(side="right", padx=10)
            pb.set(0)
            self.progress_bars[fp] = pb

    def choose_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

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
        
        params = {
            "fmt": self.output_format.get(),
            "qual": self.quality.get(),
            "exif": self.preserve_exif.get(),
            "out_dir": Path(self.output_folder.get()),
            "mode": self.resize_mode.get(),
            "wm": self.watermark_path.get(),
            "pref": self.rename_prefix.get().strip(),
            "suff": self.rename_suffix.get().strip(),
            "f_gray": self.filter_gray.get(),
            "f_auto": self.filter_auto.get(),
            "f_sharp": self.filter_sharp.get()
        }

        try:
            w, h = self.resize_width.get().strip(), self.resize_height.get().strip()
            params["resize"] = (int(w), int(h)) if w and h else None
        except:
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
                input_path=str(in_p), output_path=str(out_p), fmt=p["fmt"], quality=p["qual"], 
                resize=p["resize"], resize_mode=p["mode"], preserve_exif=p["exif"],
                watermark=p["wm"], gray=p["f_gray"], auto=p["f_auto"], sharp=p["f_sharp"]
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


def convert_image(input_path, output_path, fmt="JPEG", quality=85, resize=None, resize_mode="Stretch", preserve_exif=True, watermark="", gray=False, auto=False, sharp=False):
    # این تابع دقیقا با همان منطق قدرتمند قبلی کار می‌کند
    try:
        with Image.open(input_path) as im:
            if gray: im = im.convert("L")
            if auto:
                try: im = ImageOps.autocontrast(im.convert("RGB"))
                except: pass
            if sharp: im = im.filter(ImageFilter.SHARPEN)

            if resize:
                if resize_mode == "Fit (Maintain AR)": im = ImageOps.contain(im, resize, Image.LANCZOS)
                elif resize_mode == "Fill/Crop": im = ImageOps.fit(im, resize, Image.LANCZOS)
                else: im = im.resize(resize, Image.LANCZOS)

            kwargs = {}
            exif = im.info.get("exif") if preserve_exif and "exif" in im.info else None

            if fmt.upper() in ("JPEG", "JPG") and im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P": im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if 'A' in im.getbands() else None)
                im = bg

            if watermark and os.path.exists(watermark):
                with Image.open(watermark).convert("RGBA") as wm:
                    pos = (im.size[0] - wm.size[0] - 10, im.size[1] - wm.size[1] - 10)
                    if im.mode != "RGBA": im = im.convert("RGBA")
                    layer = Image.new("RGBA", im.size, (0,0,0,0))
                    layer.paste(wm, pos)
                    im = Image.alpha_composite(im, layer)
                    if fmt.upper() in ("JPEG", "JPG"): im = im.convert("RGB")

            if fmt.upper() in ("JPEG", "WEBP"):
                kwargs["quality"] = quality
                kwargs["optimize"] = True
            if fmt.upper() == "PNG": kwargs["compress_level"] = 6
            if exif and fmt.upper() in ("JPEG", "JPG"): kwargs["exif"] = exif

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            im.save(output_path, fmt, **kwargs)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    app = FormatoApp()
    app.mainloop()
