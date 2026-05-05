<div align="center">

# 🌌 Formato - Professional Studio
**The Ultimate All-In-One Image Processing & Exporting Tool**

![Version](https://img.shields.io/badge/Version-V1.3-blueviolet?style=for-the-badge&logo=appveyor)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Open Source](https://img.shields.io/badge/Open_Source-%E2%9D%A4-red?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C-lightgrey?style=for-the-badge)

[Explore Developer's GitHub](https://github.com/MRThugh)

</div>

---

## 📖 The Philosophy
In the modern digital workspace, content creators, developers, and photographers constantly juggle between multiple apps to resize images, compress them, add watermarks, build PDFs, and generate app icons. 

**Formato V1.3** was born out of a simple philosophy: **Zero Friction, Maximum Power**. 
It combines a sleek, modern UI (Dark Studio) with heavy-duty multithreaded processing underneath. Whether you need to process $10$ images or $10,000$ images, Formato does it flawlessly while giving you a real-time live preview of your edits.

---

## 🚀 Awesome Features

Formato is packed with professional-grade capabilities divided into three main studio modules:

### 1. ⚡ Batch Image Processor
*   **Live Preview Engine:** Instantly see changes as you tweak brightness, contrast, or watermark settings.
*   **Smart Compression:** Tell Formato your target file size (e.g., $500$ KB), and its binary-search compression algorithm will automatically find the best quality to hit that target!
*   **Intelligent Resizing:** Resize using exact $W \times H$ dimensions. Choose between *Stretch*, *Fit (Maintain Aspect Ratio)*, or *Fill/Crop*.
*   **Advanced Image Adjustments:** Tweak Brightness, Contrast, Saturation, and Sharpness on a scale from $0.2$ to $5.0$.
*   **Filters & Enhancements:** 1-click Grayscale, Auto-Contrast, and Sharpen filters.
*   **Dynamic Watermarking:** Add PNG logos, adjust opacity ($0.0$ to $1.0$), set precise positioning (Top, Bottom, Center), and define $X, Y$ margins.
*   **Metadata Manager:** Strip EXIF data for privacy, or inject custom Author tags into thousands of images at once.
*   **Preset System:** Save your perfect workflow as a `.json` preset and load it later with a single click.
*   **Multi-Threading:** Utilizes concurrent processing to utilize $100\%$ of your CPU cores for blazing-fast exports.

### 2. 📄 PDF Builder
*   Drag and drop your images, order them in the queue, and instantly compile them into a beautiful, high-quality, single-file PDF document.

### 3. 🎨 Icon & Favicon Generator
*   Select a source image and generate complete Icon/Favicon packages in milliseconds.
*   Supports standard web sizes ($16 \times 16$, $32 \times 32$) up to massive App icons ($512 \times 512$).
*   Automatically packages them into perfect `.ico` formats and high-res `.png` sets.

---

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MRThugh/Formato.git
   cd Formato
   ```
2. Install the required dependencies:
   ```bash
   pip install customtkinter Pillow tkinterdnd2
   ```
   *(Note: `tkinterdnd2` is optional but highly recommended to enable Drag & Drop features!)*

3. Run the application:
   ```bash
   python main.py
   ```

---

## 🎮 How to Use (V1.3)

### Batch Processing Images
1. **Add Files:** Drag & drop images into the "Queue" area, or use the `➕ Add Files` button.
2. **Preview:** Click on any file in the queue to load it into the **Live Preview** panel.
3. **Tweak Settings:** 
   * Select your output format (JPEG, PNG, WEBP, TIFF, BMP).
   * Apply filters, adjust dimensions, or set up a watermark.
   * *Pro-tip: Enable "Smart Compression" to keep files under a specific KB size!*
4. **Select Destination:** Click the folder icon 📁 at the bottom right to choose where the processed files will be saved.
5. **Start:** Hit **🚀 START PROCESSING**.

### Exporting to PDF
1. Go to the **📄 PDF Export** tab on the left sidebar.
2. Ensure you have added your images to the Queue (in the Batch tab).
3. Click **Export to PDF**, choose your save location, and Formato will combine them instantly.

### Generating Icons
1. Go to the **🎨 Icon Generator** tab.
2. Select your high-resolution source image.
3. Choose your target type (*Favicon* or *App Icon*) to auto-select standard sizes, or manually check the sizes you need.
4. Click **⚡ Generate Icons** and pick a save folder.

---

## 👨‍💻 Author

Created with ❤️ by **Ali Kamrani**

*   GitHub: [@MRThugh](https://github.com/MRThugh)

Feel free to star ⭐ the repository if you find this tool helpful, and open issues or pull requests to contribute to the next version!

---
<div align="center">
  <sub>Built with Python & CustomTkinter</sub>
</div>
