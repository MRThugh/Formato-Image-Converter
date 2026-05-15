# 🎨 Formato - Professional Image Processing Studio

<p align="center">
  <img src="assets/logo.png" alt="Formato Logo" width="180">
</p>

<p align="center">
  <strong>A powerful and modern desktop application for batch image processing, PDF generation, and icon creation.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/GUI-CustomTkinter-1f6feb?style=for-the-badge">
  <img src="https://img.shields.io/badge/Pillow-Image%20Processing-ff9800?style=for-the-badge">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Developed%20by-MRThugh-black?style=for-the-badge">
  <img src="https://img.shields.io/badge/Version-2.0.0-purple?style=for-the-badge">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge">
</p>

---

## 🚀 Overview

**Formato** is a professional-grade image processing suite built with Python and CustomTkinter.  
It combines advanced batch conversion, live preview, watermarking, metadata editing, PDF exporting, and favicon/icon generation in a sleek desktop interface.

Designed and developed by [MRThugh](https://github.com/MRThugh?utm_source=chatgpt.com), Formato demonstrates modern Python desktop engineering with multithreading, drag-and-drop support, and real-time image rendering.

---

## ✨ Key Features

### ⚡ Batch Image Processing
- Convert images to JPEG, PNG, WEBP, TIFF, and BMP
- Multi-threaded high-speed processing
- Individual progress bars for each file
- Drag & Drop support

### 👁️ Live Preview Engine
- Real-time image preview
- Debounced rendering for smooth performance
- Instant updates while adjusting settings

### 📏 Smart Resize
- Stretch
- Fit while maintaining aspect ratio
- Fill and crop
- Automatic dimension calculation

### 🎨 Advanced Adjustments
- Brightness
- Contrast
- Saturation
- Sharpness

### 🧠 Smart Compression
- Target file size in KB
- Binary search quality optimization
- Automatic best-quality output

### 🖼️ Watermark System
- PNG watermark support with transparency
- Adjustable size and opacity
- Custom margins
- Multiple placement options

### 🏷️ Metadata Management
- Preserve original EXIF data
- Add custom author/artist metadata

### 📄 PDF Builder
- Combine multiple images into a single PDF

### 🎨 Icon & Favicon Generator
- Generate `.ico` files
- Export multiple PNG sizes
- Web and application presets

### 💾 Preset System
- Save settings to JSON
- Load saved configurations instantly

---

## 🖼️ Supported Formats

| Input | Output |
|------|------|
| JPG / JPEG | JPEG |
| PNG | PNG |
| WEBP | WEBP |
| TIFF | TIFF |
| BMP | BMP |
| GIF | BMP / PNG / JPEG / WEBP |

---

## 🛠️ Technology Stack

- :contentReference[oaicite:1]{index=1}
- :contentReference[oaicite:2]{index=2}
- :contentReference[oaicite:3]{index=3}
- :contentReference[oaicite:4]{index=4}
- :contentReference[oaicite:5]{index=5}

---

## 📦 Installation

```bash
git clone https://github.com/MRThugh/Formato.git
cd Formato
pip install -r requirements.txt
python formato.py
````

---

## 📋 Requirements

```txt
customtkinter
Pillow
tkinterdnd2
```

---

## 🏗️ Architecture Highlights

* Object-Oriented design
* Modular helper functions
* Multi-threaded processing
* Real-time preview engine
* Smart compression algorithm
* JSON-based preset management

---

## 🧠 Notable Algorithms

### Binary Search Smart Compression

Formato automatically finds the highest possible image quality while staying below a user-defined file size limit.

### Debounced Live Preview

Rendering updates are delayed intelligently to prevent excessive processing during rapid adjustments.

### Concurrent Batch Processing

Multiple images are processed simultaneously using Python's `ThreadPoolExecutor`.

---

## 🎯 Project Goals

Formato was created to provide:

* Professional image processing tools
* Modern desktop UI/UX
* Efficient multi-threaded performance
* Real-world utility for developers and designers
* A showcase of advanced Python engineering skills

---

## 👨‍💻 Developer

**Ali Kamrani**
GitHub: [MRThugh](https://github.com/MRThugh?utm_source=chatgpt.com)

---

## 🌟 Why This Project Matters

Formato is more than an image converter. It is a complete desktop application demonstrating:

* Advanced GUI development
* Image processing expertise
* Multithreading
* File handling
* Metadata management
* Software architecture principles

This project reflects the technical growth and engineering mindset of its developer, [MRThugh](https://github.com/MRThugh?utm_source=chatgpt.com).

---

## 📜 License

MIT License

---

## ⭐ Support the Project

If you find this project useful, please consider starring the repository on [GitHub](https://github.com/MRThugh/Formato?utm_source=chatgpt.com).

<p align="center">
  <strong>Built with passion by Ali Kamrani (MRThugh)</strong>
</p>
```
