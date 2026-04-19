# 🎨 Formato - Professional Studio

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-Dark_UI-2b2b2b?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Formato** is a powerful, completely free, and open-source all-in-one desktop studio built with Python. It has been completely redesigned to provide professional-grade tools for batch image processing, PDF compilation, and icon generation, all wrapped in a sleek, non-blocking Dark Studio interface powered by **CustomTkinter**.

---

## ✨ What's New in This Version?
- **PDF Builder:** Combine multiple images into a single PDF document instantly.
- **Advanced Batch Processing:** Multi-threaded processing for zero UI freezing.
- **Smart Resize:** Choose between Stretch, Fit (Maintain Aspect Ratio), or Fill/Crop.
- **Enhancements:** Apply Grayscale, Auto-Contrast, and Sharpen filters on the fly.
- **Watermark & Renaming:** Automatically overlay PNG logos and batch rename files with custom prefixes/suffixes.

---

## 🔥 Key Features

### ⚡ Batch Image Processor
- Convert between multiple formats (JPEG, PNG, WEBP, TIFF, BMP).
- Real-time progress tracking per file and overall progress.
- Full control over output quality and EXIF metadata preservation.
- Apply custom PNG watermarks to hundreds of images at once.
- Automated batch renaming (Prefix & Suffix).

### 📄 PDF Builder
- Select multiple images from your queue and compile them into a single, high-quality `.pdf` file.
- Perfect for creating portfolios, reports, or document scanning compilation.

### 🎨 Icon / Favicon Generator
- Generate professional **favicons** and **application icons** in all standard sizes:
  - $16\times16$, $32\times32$, $48\times48$, $64\times64$, $128\times128$
  - $180\times180$ (Apple Touch Icon)
  - $192\times192$ (Android Chrome / PWA)
  - $256\times256$ (Best compatibility with Windows)
  - $512\times512$ (Large icon for web app manifest)
- Generates both a compiled `.ico` file and separate `.png` files.

---

## 📸 Screenshots

<div align="center">
  <!-- Note: Update these image paths with your actual screenshots -->
  <img src="assets/batch_tab.png" width="32%" alt="Batch Processor Tab" />
  <img src="assets/pdf_tab.png" width="32%" alt="PDF Builder Tab" />
  <img src="assets/icon_tab.png" width="32%" alt="Icon Generator Tab" />
</div>

---

## 💾 Download & Installation

**[Download the latest release (Windows)](https://github.com/MRThugh/Formato-Image-Converter/releases/latest)**

- Professional installer with custom icon and optional desktop shortcut.
- Standalone executable (No Python installation required).

### For Developers (Run from Source)
1. Clone the repository:
```bash
   git clone https://github.com/MRThugh/Formato-Image-Converter.git
   cd Formato-Image-Converter
```


## 💾 Download & Installation

**[Download the latest release (Windows)](https://github.com/MRThugh/Formato-Image-Converter/releases/latest)**

- Professional installer with custom icon and optional desktop shortcut.
- Standalone executable (No Python installation required).

### For Developers (Run from Source)
1. Clone the repository:
   ```bash
   git clone https://github.com/MRThugh/Formato-Image-Converter.git
   cd Formato-Image-Converter
   ```
2. Install dependencies:
   ```bash
   pip install customtkinter Pillow
   ```
3. Run the application:
   ```bash
   python main.py
   ```

---

## 🤝 Contributing
Contributions are very welcome! Whether it's bug reports, feature suggestions, or code improvements (like optimizing the multi-threading or adding new filters) — feel free to:

1. Open an Issue
2. Submit a Pull Request

We appreciate all help in making Formato even better ❤️

---

**Built in silence by [MRThugh](https://github.com/MRThugh)**  
⭐ If you find Formato useful, please give it a star — it means a lot


   
