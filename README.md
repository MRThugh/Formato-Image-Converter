# Formato - Professional Image Studio 🎨✨

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-PySide6%20%2F%20Qt6-brightgreen.svg)](https://wiki.qt.io/Qt_for_Python)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[**Formato**](https://github.com/MRThugh/Formato-Image-Converter) is a versatile, modern desktop application designed for batch image processing, optimization, and conversion. Built using the powerful **PySide6** (Qt for Python) framework and the **Pillow (PIL)** imaging library, it provides an efficient, lightweight, and responsive workspace for creators and developers alike.

The codebase has been refactored into a clean, modular architecture. This separation of concerns improves performance, code readability, and makes it easily extensible for future feature integrations.

---

## 🚀 Core Features

- **Batch Processing:** Concurrently convert files to widely-used formats including `JPEG`, `PNG`, `WEBP`, `TIFF`, `BMP`, and `GIF`.
- **Smart Compression:** Adjust output quality manually or utilize smart compression to automatically approximate a target file size (in KB) using an efficient iterative search algorithm.
- **Smart Resizing:** Resize images using Stretch, Fit (maintain aspect ratio), or Fill/Crop modes.
- **Advanced Adjustments:** Fine-tune brightness, contrast, saturation, and sharpness using smooth sliders. Double-click any label to quickly reset its value.
- **Visual Filters:** Apply pre-defined filters such as Grayscale, Auto-Contrast, Sharpen, Blur, Contour, Emboss, and Edge Enhance.
- **Metadata Management:** Preserve original EXIF data or write custom metadata (Author, Copyright, and Description) to supported formats.
- **Advanced Watermarking:** Load a PNG logo watermark, adjust its position (5 placement zones), scale, opacity, and custom pixel margins.
- **Live Interactive Preview:** Pan (drag) and zoom (scroll) on an interactive graphics scene with integrated RAM image caching to deliver fast, real-time feedback.
- **PDF Builder:** Merge selected queue images into a single, multi-page PDF document.
- **Icon & Favicon Generator:** Generate individual resolution assets for web or app platforms and compile them into a unified multi-size `.ico` file.

---

## 🛠 Tech Stack

- **Core Language:** Python 3.10+
- **Graphical User Interface:** PySide6 (Qt6) with a customized, premium dark QSS theme.
- **Image Manipulation:** Pillow (PIL)
- **Concurrency:** Built-in multi-threading utilizing `ThreadPoolExecutor` to handle background image processing and thumbnail rendering, ensuring the main GUI remains responsive and lag-free.

---

## 📂 Project Architecture

The repository is organized following clean-coding principles to separate data, logic, and interface elements:

```text
formato_project/
│
├── assets/                    # Static assets (logos, icons, and favicon.ico)
│   ├── logo.png
│   └── icon.ico
│
├── core/                      # Image processing core using Pillow algorithms
│   ├── __init__.py
│   └── image_processor.py
│
├── models/                    # Data representations and Model-View architectures
│   ├── __init__.py
│   └── queue_model.py
│
├── views/                     # UI components, custom widgets, and windows
│   ├── __init__.py
│   ├── widgets.py             # Zoomable canvas, smooth scroll area, and delegate rendering
│   └── main_window.py         # Primary window controller and interface setups
│
├── config.py                  # Static configurations, file paths, and CSS stylesheets
├── utils.py                   # General-purpose utility and mathematical helpers
├── requirements.txt           # Project dependencies
└── main.py                    # Application entry point
```

---

## 📦 Installation & Setup

Ensure you have Python 3.10 or higher installed on your system.

1. Clone the repository:
```bash
git clone https://github.com/MRThugh/Formato-Image-Converter.git
cd Formato-Image-Converter
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Launch the application:
```bash
python main.py
```

---

## ⚙️ How to Use

1. **Manage the Queue:** Add files using the `➕ Add Files` button or drag-and-drop images directly into the interface. Click any item to display its real-time preview. To remove an image, click the red deletion mark (`×`) on the right side of the queue item.
2. **Configure Settings:** Choose your destination format, resize parameters, rename rules (prefix/suffix), and any desired filters.
3. **Save/Load Presets:** Easily export your preferred settings configurations via `Save Preset` as a JSON file, and reload them later using `Load Preset`.
4. **Choose Destination:** Specify your output directory, then click `🚀 START PROCESSING` to run the concurrent batch converter.

---

## 🤝 Contributing

Contributions make the open-source community a better place to learn, inspire, and create. Any contributions you make are greatly appreciated.

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📝 License

Distributed under the MIT License. See the `LICENSE` file in the repository for more details.
