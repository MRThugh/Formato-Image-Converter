"""
Main Tkinter GUI for formato.
Run with: python -m formato.app or python formato/app.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, queue, os
from pathlib import Path

from formato import converter
from formato.utils import setup_logger, ensure_output_folder
from formato.gui_widgets import FileListFrame

logger = setup_logger()

class FormatoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("formato — Image Format Converter")
        self.geometry("800x520")
        self.minsize(700,420)
        self.queue = queue.Queue()
        self.selected_files = []
        self.output_folder = Path.cwd() / "formato_output"
        ensure_output_folder(self.output_folder)
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        # keyboard shortcuts
        self.bind_all("<Control-o>", lambda e: self.select_files())
        self.bind_all("<Control-q>", lambda e: self.on_quit())

    def _build_ui(self):
        # Top controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        btn_files = ttk.Button(top, text="Select Files", command=self.select_files)
        btn_files.pack(side="left")
        btn_folder = ttk.Button(top, text="Select Folder", command=self.select_folder)
        btn_folder.pack(side="left", padx=6)
        ttk.Label(top, text="Output folder:").pack(side="left", padx=(12,4))
        self.output_entry = ttk.Entry(top, width=40)
        self.output_entry.pack(side="left")
        self.output_entry.insert(0, str(self.output_folder))
        ttk.Button(top, text="Browse", command=self.select_output).pack(side="left", padx=4)

        # Middle: file list and options
        middle = ttk.Frame(self)
        middle.pack(fill="both", expand=True, padx=8, pady=6)
        left = ttk.Frame(middle)
        left.pack(side="left", fill="both", expand=True)
        self.file_list = FileListFrame(left)
        self.file_list.pack(fill="both", expand=True)

        right = ttk.Frame(middle, width=260)
        right.pack(side="right", fill="y", padx=(8,0))
        ttk.Label(right, text="Output format:").pack(anchor="w", pady=(4,0))
        self.format_var = tk.StringVar(value="JPEG")
        for v in ("JPEG","PNG","WEBP","BMP","TIFF"):
            ttk.Radiobutton(right, text=v, variable=self.format_var, value=v).pack(anchor="w")

        ttk.Label(right, text="Quality:").pack(anchor="w", pady=(8,0))
        self.quality = tk.IntVar(value=85)
        ttk.Scale(right, from_=1, to=100, variable=self.quality, orient="horizontal").pack(fill="x", pady=(0,6))

        # Resize option
        self.resize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(right, text="Resize (width px)", variable=self.resize_var, command=self._toggle_resize).pack(anchor="w", pady=(6,0))
        self.width_var = tk.IntVar(value=800)
        self.width_entry = ttk.Entry(right, textvariable=self.width_var, state="disabled")
        self.width_entry.pack(fill="x")

        # EXIF checkbox
        self.exif_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right, text="Preserve EXIF (best-effort)", variable=self.exif_var).pack(anchor="w", pady=(8,0))

        # Overwrite option
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(right, text="Overwrite existing", variable=self.overwrite_var).pack(anchor="w", pady=(8,0))

        # Convert button
        self.convert_btn = ttk.Button(right, text="Convert", command=self.start_conversion)
        self.convert_btn.pack(fill="x", pady=(12,6))

        # Progress and log
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=(0,8))
        self.progress = ttk.Progressbar(bottom, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x")
        self.log_text = tk.Text(bottom, height=6)
        self.log_text.pack(fill="x", pady=(6,0))

    def _toggle_resize(self):
        state = "normal" if self.resize_var.get() else "disabled"
        self.width_entry.config(state=state)

    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        logger.info(msg)

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select images",
                                            filetypes=[("Images","*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),("All files","*.*")])
        if files:
            self.add_files(files)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            # add image files in folder
            exts = (".png",".jpg",".jpeg",".webp",".bmp",".tiff",".tif")
            files = [str(p) for p in Path(folder).iterdir() if p.suffix.lower() in exts]
            self.add_files(files)

    def add_files(self, files):
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                p = Path(f)
                fmt = p.suffix.replace(".","").upper()
                try:
                    size = f"{p.stat().st_size//1024} KB"
                except Exception:
                    size = "N/A"
                self.file_list.add(p.name, fmt, size)
        self.log(f"Added {len(files)} file(s). Total: {len(self.selected_files)}")

    def select_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_entry.delete(0,"end")
            self.output_entry.insert(0, folder)
            self.output_folder = Path(folder)

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("No files", "Please select files to convert.")
            return
        out_folder = Path(self.output_entry.get() or self.output_folder)
        out_folder.mkdir(parents=True, exist_ok=True)
        # disable UI
        self.convert_btn.config(state="disabled")
        self.progress["value"] = 0
        total = len(self.selected_files)
        self.progress["maximum"] = total
        # spawn thread
        t = threading.Thread(target=self._conversion_worker, args=(list(self.selected_files), out_folder))
        t.daemon = True
        t.start()
        # poll queue for updates
        self.after(200, self._poll_queue)

    def _conversion_worker(self, files, out_folder):
        successes = 0
        failures = 0
        errors = []
        for idx, f in enumerate(files, start=1):
            try:
                src = Path(f)
                target_name = src.stem + "." + self.format_var.get().lower()
                dest = out_folder / target_name
                if dest.exists() and not self.overwrite_var.get():
                    # skip or rename
                    dest = out_folder / (src.stem + "_converted." + self.format_var.get().lower())
                # determine resize
                resize = None
                if self.resize_var.get():
                    try:
                        w = int(self.width_var.get())
                        # preserve aspect ratio: open to compute height
                        from PIL import Image
                        with Image.open(src) as im:
                            ratio = im.height / im.width
                            resize = (max(1,int(w)), max(1,int(w*ratio)))
                    except Exception:
                        resize = None
                res = converter.convert_image(src, dest, fmt=self.format_var.get(), quality=self.quality.get(),
                                              resize=resize, preserve_exif=self.exif_var.get())
                if res["success"]:
                    successes += 1
                    self.queue.put(("log", f"Converted: {src.name} -> {dest.name}"))
                else:
                    failures += 1
                    errors.append((src.name, res["error"]))
                    self.queue.put(("log", f"Error converting {src.name}: {res['error']}"))
            except Exception as e:
                failures += 1
                errors.append((f, str(e)))
                self.queue.put(("log", f"Exception: {e}"))
            self.queue.put(("progress", 1))
        # final summary
        self.queue.put(("done", {"successes": successes, "failures": failures, "errors": errors, "out_folder": str(out_folder)}))

    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == "log":
                    self.log(item[1])
                elif item[0] == "progress":
                    self.progress.step(item[1])
                elif item[0] == "done":
                    data = item[1]
                    self.log(f"Done. Successes: {data['successes']}, Failures: {data['failures']}")
                    if data["failures"] > 0:
                        self.log("Errors: " + "; ".join(f"{e[0]}: {e[1]}" for e in data["errors"]))
                    # enable UI
                    self.convert_btn.config(state="normal")
                    if Path(data["out_folder"]).exists():
                        if messagebox.askyesno("Open folder", "Conversion finished. Open output folder?"):
                            import subprocess, sys
                            if sys.platform.startswith("win"):
                                subprocess.Popen(["explorer", data["out_folder"]])
                            elif sys.platform.startswith("darwin"):
                                subprocess.Popen(["open", data["out_folder"]])
                            else:
                                subprocess.Popen(["xdg-open", data["out_folder"]])
                    return
        except Exception:
            pass
        # keep polling
        self.after(200, self._poll_queue)

    def on_quit(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

def main():
    app = FormatoApp()
    app.mainloop()

if __name__ == "__main__":
    main()
