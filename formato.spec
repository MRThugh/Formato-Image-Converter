# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

assets_dir = Path("assets")
datas = [
    (str(assets_dir), "assets"),
]

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PIL",
    "PIL.Image",
    "PIL.ImageOps",
    "PIL.ImageFilter",
    "PIL.ImageEnhance",
    "PIL.IcoImagePlugin",
    "PIL.WebPImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.PngImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.BmpImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.PdfImagePlugin",
]

excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "pytest",
    "unittest",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Formato",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico" if sys.platform.startswith("win") else None,
)
