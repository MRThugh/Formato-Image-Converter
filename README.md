# Formato — Professional Desktop Image Studio

<p align="center">
  <img src="assets/logo.png" alt="Formato Logo" width="128" height="128">
</p>

<p align="center">
  <strong>High-performance, Native Cross-Platform Desktop Image Processing & Conversion Studio</strong><br>
  Built with Python 3.11+, PySide6 (Qt6), and Pillow.
</p>

<p align="center">
  <a href="https://github.com/MRThugh/Formato-Image-Converter"><img src="https://img.shields.io/badge/GitHub-MRThugh%2FFormato--Image--Converter-blue?logo=github" alt="GitHub Repo"></a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?logo=qt&logoColor=white" alt="PySide6 / Qt6">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Cross-Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

---

## 🌟 Overview

**Formato** is a native, professional desktop application engineered for batch image conversion, smart compression, color grading, watermarking, multi-resolution icon authoring, and multi-page PDF compilation.

Unlike browser-based wrappers or heavy electron apps, Formato runs **100% locally and natively** on your machine with minimal resource overhead, thread-safe asynchronous execution, and real-time live previewing.

---

## ✨ Key Features

### 🗂 Batch Image Converter
- **Multi-Format Support**: High-fidelity conversion across **JPEG, PNG, WEBP, TIFF, BMP, and GIF**.
- **Collision-Safe Export**: Never overwrites existing files — automatically resolves duplicate filenames cleanly (`photo_1.webp`, `photo_2.webp`) with atomic write protection.
- **Smart Compression**: Intelligent binary search algorithm to target specific file sizes (e.g. 150 KB) without manual trial-and-error.
- **Aspect-Ratio Resizing**:
  - **Fit**: Constrains inside a bounding box while strictly maintaining aspect ratio.
  - **Fill / Crop**: Centers and crops edges to achieve an exact dimensional canvas.
  - **Stretch**: Scaled directly to specified pixel bounds.
- **Color & Tonal Grading**: Real-time Brightness, Contrast, Saturation, and Sharpness controls.
- **Artistic & Utility Filters**: Grayscale, Auto-Contrast, Edge Enhancement, Sharpen, Blur, Contour, and Emboss.
- **Visual Watermarking**: Real-time PNG watermark overlays with opacity, size scaling, and margin offsets.
- **EXIF & Metadata Engine**: Preserve original camera EXIF or inject custom Author, Copyright, and Description tags.
- **Thread-Safe Queue & Live Counter**: Visual progress tracking, item deletion, and real-time counter (`Queue · 5 Files`).
- **Instant Cancellation**: Interrupt batch jobs safely at any moment without leaving corrupted or half-written files.

### 📄 Multi-Page PDF Builder
- Memory-efficient image-to-PDF compilation.
- Supports **A4, A5, Letter, and Original** page sizes with custom orientation (Portrait / Landscape), Fit/Fill sizing, and configurable page margins.

### 🎨 Icon & Favicon Generator
- Master image downsampling into multi-resolution Windows `.ico` files containing embedded 16×16, 32×32, 48×48, 64×64, 128×128, and 256×256 px mipmaps.

### 💾 Preset Management
- Save and load complete workspace configurations to portable `.json` files.

---

## 🏗 Native Desktop Architecture

```
Formato/
├── core/                       # Core Image Processing Engine
│   ├── pipeline.py             # Single unified processing pipeline (Preview & Batch)
│   ├── watermark.py            # Watermark overlay calculation & safe coordinate clamping
│   ├── pdf_builder.py          # Memory-efficient multi-page PDF generation
│   └── icon_builder.py         # Multi-size Windows .ico generator
├── models/                     # Data Models & Qt Models
│   ├── conversion_settings.py  # Dataclass with validation & clamping
│   └── queue_model.py          # Thread-safe QAbstractListModel with thumbnail caching
├── views/                      # Native Qt6 User Interface
│   ├── main_window.py          # Main Window, Sidebar navigation, and Workspaces
│   └── widgets.py              # Custom Qt Widgets & Item Delegates
├── workers/                    # Asynchronous Threading
│   ├── conversion_worker.py    # QThread batch processing with Signal/Slot communication
│   ├── preview_worker.py       # Debounced, cancellable live preview worker
│   └── pdf_worker.py           # Background PDF export worker
├── utils/                      # Utilities & Helpers
│   ├── paths.py                # Cross-platform asset, log, and runtime path resolver
│   ├── logging.py              # Centralized logging engine
│   ├── filenames.py            # Collision-proof unique output paths & atomic file writes
│   └── helpers.py              # Dimension math and conversions
├── assets/                     # Application Icons and Branding
├── tests/                      # Automated Unit Test Suite (30 Tests)
├── config.py                   # Centralized Configuration & Dark QSS Theme
├── formato.spec                # PyInstaller executable specification
└── main.py                     # Native desktop entry point
```

### Threading & Safety Guarantees
- **No UI Touches from Background Threads**: Worker threads communicate strictly via Qt Signals (`file_progress`, `file_completed`, `overall_progress`, `batch_finished`).
- **Atomic Disk Writes**: Files are written to hidden temporary files first and atomically swapped upon successful completion.
- **Safe Watermark Clamping**: Watermarks larger than the target canvas are scaled down dynamically, eliminating coordinate overflow bugs.

---

## 🚀 Installation & Local Execution

### Prerequisites
- Python 3.11 or higher
- `pip`

### 1. Clone the Repository
```bash
git clone https://github.com/MRThugh/Formato-Image-Converter.git
cd Formato-Image-Converter
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python3 -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

---

## 🧪 Running the Test Suite

Formato includes a comprehensive test suite covering all image transformations, smart compression, EXIF preservation, filename collisions, watermark clamping, and PDF compilation:

```bash
python -m unittest discover -s tests -v
```

---

## 📦 Building Standalone Executables (PyInstaller)

To build standalone, single-file or directory binaries for distribution:

### Using the Included PyInstaller Spec:
```bash
pip install pyinstaller
pyinstaller formato.spec --noconfirm
```

The output executable will be placed in the `dist/` directory:
- **Windows**: `dist/Formato.exe`
- **Linux**: `dist/Formato`
- **macOS**: `dist/Formato.app`

---

## 🌐 Automated CI/CD & Releases

The repository includes a GitHub Actions workflow (`.github/workflows/build.yml`) that automatically:
1. Runs the full unit test suite across Python 3.11.
2. Builds native executables and installers:
   - **Windows**: Inno Setup installer (`.exe`)
   - **macOS**: Apple Disk Image (`.dmg`)
   - **Linux**: Standalone `.tar.gz` archive
3. Automatically publishes GitHub Releases with release assets whenever a version tag (e.g. `v2.6.0`) is pushed.

---

## 👨‍💻 Author & Credits

- **Developer**: Ali Kamrani ([@MRThugh](https://github.com/MRThugh))
- **Repository**: [MRThugh/Formato-Image-Converter](https://github.com/MRThugh/Formato-Image-Converter)
- **License**: Released under the [MIT License](LICENSE).
