# 🎨 Formato - Professional Image Processing Studio

<p align="center">
  <img src="logo.png" alt="Formato Logo" width="180">
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
  <img src="https://img.shields.io/badge/Version-2.1.0-purple?style=for-the-badge">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge">
</p>

---

## 🚀 Overview

**Formato** is a professional-grade image processing suite built with Python and CustomTkinter. It combines advanced batch conversion, optimized live preview, EXIF metadata editing, watermarking, multi-frame GIF preservation, PDF exporting, and multi-size icon generation into a unified, user-friendly desktop experience.

Designed and developed by [MRThugh](https://github.com/MRThugh), Formato demonstrates modern Python desktop engineering utilizing multithreading, system-level drag-and-drop integration, and optimized pipeline-oriented rendering.

---

## ✨ Key Features

### ⚡ Batch Image Processing & Formats
- Convert images in bulk to JPEG, PNG, WEBP, TIFF, BMP, and GIF.
- Fully multithreaded engine utilizing a thread pool for parallel operations.
- **Drag & Drop support** to load hundreds of files instantly.
- Live progress tracking with individual progress bars for each queued item.

### 📋 Queue Management with Thumbnails
- **Real-time Thumbnails:** Generates a lightweight 40x40 visual thumbnail for each file in the queue.
- **Individual File Removal:** Remove single files from the list instantly using the `❌` button without clearing the whole queue.

### 👁️ High-Performance Live Preview
- **Pre-Scaled Processing:** Automatically downscales high-resolution images to a lightweight proxy size before applying enhancements, removing UI lag even on large 4K or RAW files.
- Real-time previews of adjustments, watermarks, resizing modes, and filters.
- Debounced preview thread rendering to save processing overhead during slider drags.

### 📏 Smart Resize Modes
- **Stretch:** Force coordinates to exact custom dimensions.
- **Fit (Maintain AR):** Resize cleanly within bounds without stretching.
- **Fill / Crop:** Automatically fill dimensions and crop out excessive margins.
- Keeps original aspect ratio intact automatically if only one dimension is entered.

### 🎨 Advanced Adjustments & Filters
- Precision sliders for Brightness, Contrast, Saturation, and Sharpness.
- Quick double-click to reset sliders back to the initial `1.0` value.
- Filters: Grayscale conversion, Image Sharpen, and Auto-Contrast.

### 🧠 Smart RAM-Based Compression
- Compress target outputs down to a specific size in KB.
- Utilizes an in-memory binary search quality optimizer (`io.BytesIO`) to protect SSD/HDD from redundant writes.

### 🖼️ Watermark System
- Supports PNG logo watermarks with transparency overlay.
- Position presets (Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center).
- Seamless opacity, size, and margin configuration.
- **Monochrome-Safe Mode:** Seamlessly handles watermarks on Grayscale (`L` mode) canvasses by managing temporary color spaces without corrupting the alpha channels.

### 🏷️ Expanded Metadata Management
- Preserve original camera EXIF data.
- **Expanded EXIF Compiler:** Inject custom values for **Author/Artist**, **Copyright Info**, and **Image Description/Caption** directly into standard EXIF headers (Tags 315, 33432, 270).

### 📄 PDF Builder
- Combine multiple images in the queue into a single PDF document.
- Safely flattens transparent PNG elements over a white solid canvas to avoid PDF transparency conversion errors.

### 🎨 Icon & Favicon Generator
- Export multiple PNG icon sizes alongside native `.ico` master files.
- Presets optimized for Web Favicons or Desktop Application requirements.

### 💾 Preset System
- Save current slider values, text configurations, and dimensions to a local JSON file.
- Load custom configurations instantly for a faster workflow.

---

## 🖼️ Supported Formats

| Input Format | Output Format | Dynamic Frame Preservation (GIF) |
| :--- | :--- | :--- |
| **JPG / JPEG** | JPEG, PNG, WEBP, TIFF, BMP, GIF | N/A |
| **PNG** | JPEG, PNG, WEBP, TIFF, BMP, GIF | N/A |
| **WEBP** | JPEG, PNG, WEBP, TIFF, BMP, GIF | N/A |
| **TIFF** | JPEG, PNG, WEBP, TIFF, BMP, GIF | N/A |
| **BMP** | JPEG, PNG, WEBP, TIFF, BMP, GIF | N/A |
| **GIF** | JPEG, PNG, WEBP, TIFF, BMP, GIF | **Yes (Full frame-by-frame animation processed & preserved)** |

---

## 🛠️ Technology Stack

- **Python 3.10+**: Core programming language.
- **CustomTkinter**: Modern dark-themed responsive desktop GUI wrapper.
- **Pillow (PIL)**: High-performance advanced image processing, canvas operations, EXIF compiler, and multi-frame parsing.
- **TkinterDnD2**: Native cross-platform drag-and-drop file subsystem integration.

---

## 📦 Installation

To run Formato locally, clone the repository and install the dependencies:

```bash
git clone https://github.com/MRThugh/Formato.git
cd Formato
pip install -r requirements.txt
python formato.py
```

---

## 📋 Requirements

Save the following requirements to your `requirements.txt` file:

```txt
customtkinter>=5.2.0
Pillow>=10.0.0
tkinterdnd2>=0.3.0
```

---

## 🏗️ Architecture Highlights

* **Object-Oriented Design:** Clear segregation of GUI states, helper functions, and background threads.
* **Pre-Processing Validations:** Actively validates the queue, verifies output folder path presence, and tests disk write permissions by writing/removing temporary tokens before spawning conversion threads.
* **Asynchronous Execution:** Thread Pool Executor ensures multiple large image files are processed concurrently without freezing the main application thread.

---

## 🧠 Notable Algorithms

### RAM-Buffered Binary Search Quality Matcher
Instead of committing multiple experimental files to disk, Formato handles binary search iterations within RAM using memory streams (`io.BytesIO`). It evaluates file output sizes against the target KB threshold and commits to storage only once when the optimal quality setting is calculated.

### Smooth Debounced Preview Proxy
During live adjustments, Formato dynamically downsamples the target image workspace to an optimal thumbnail size on a separate thread. This design removes rendering pipeline bottlenecks and ensures adjustments are instantaneous and smooth.

### Animated Frame-by-Frame Processing
For animated GIFs, Formato tracks active frames, extracts, transforms, applies adjustments and watermarks to each frame individually, and compiles them back together while accurately preserving loop count and frame-rate durations.

---

## 🎯 Project Goals

Formato was created to provide:
* A modern desktop GUI/UX following professional dark UI design principles.
* Efficient, optimized, and multi-threaded processing of complex file operations.
* A practical, real-world utility demonstrating advanced Python engineering, clean code architecture, and efficient asset handling.

---

## 👨‍💻 Developer

**Ali Kamrani**
- GitHub: [MRThugh](https://github.com/MRThugh)

---

## 🌟 Why This Project Matters

Formato is more than a batch converter. It is a production-ready showcase of:
* Software engineering principles and asynchronous programming.
* Rigorous input/validation testing and reliable exception handling.
* Advanced layout engineering with GUI frameworks.
* Complete image editing pipeline design (filters, transforms, watermarks, metadata, and container building).

---

## 📜 License

This project is licensed under the MIT License.

---

## ⭐ Support the Project

If you find this project useful or educational, please consider giving the repository a star on [GitHub](https://github.com/MRThugh/Formato).

<p align="center">
  <strong>Built with passion by Ali Kamrani (MRThugh)</strong>
</p>
```
