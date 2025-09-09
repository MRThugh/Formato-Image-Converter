"""
Converter logic for formato.
Provides batch conversion with basic EXIF preservation and threading to avoid blocking GUI.
"""
from PIL import Image, UnidentifiedImageError
from pathlib import Path
import os
import traceback

def convert_image(input_path, output_path, fmt="JPEG", quality=85, resize=None, preserve_exif=True, background=(255,255,255)):
    """
    Convert a single image.
    - input_path: Path-like to input file
    - output_path: Path-like where to save output (including extension)
    - fmt: Pillow format string, e.g. "JPEG", "PNG", "WEBP"
    - quality: int 1-100 for lossy formats
    - resize: tuple (width, height) or None
    - preserve_exif: try to preserve EXIF bytes for JPEG when possible
    - background: RGB tuple used to composite alpha channels when target doesn't support alpha
    Returns: dict with keys: success (bool), error (str or None)
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    try:
        with Image.open(input_path) as im:
            original_mode = im.mode
            # Resize if requested
            if resize:
                im = im.resize(resize, Image.LANCZOS)
            save_kwargs = {}
            # Try to preserve EXIF raw bytes if possible
            exif_bytes = None
            if preserve_exif and "exif" in im.info:
                exif_bytes = im.info.get("exif")
            # Handle alpha for formats without alpha (JPEG)
            if fmt.upper() in ("JPEG","JPG") and im.mode in ("RGBA","LA","P"):
                # Composite over white background by default
                bg = Image.new("RGB", im.size, background)
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1])  # paste with alpha
                im = bg
            # For PNG/WebP, allow RGBA
            if fmt.upper() in ("PNG","WEBP","TIFF") and im.mode == "RGBA":
                save_kwargs["compress_level"] = 6
            # quality
            if fmt.upper() in ("JPEG","WEBP"):
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True
            # EXIF
            if exif_bytes and fmt.upper() in ("JPEG","JPG"):
                save_kwargs["exif"] = exif_bytes
            # Ensure parent exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            im.save(output_path, fmt, **save_kwargs)
        return {"success": True, "error": None}
    except UnidentifiedImageError as e:
        return {"success": False, "error": f"UnidentifiedImageError: {e}"}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}\\n{traceback.format_exc()}"}