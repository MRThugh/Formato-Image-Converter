import os
from pathlib import Path
from typing import Tuple, Dict, Any, Union
from PIL import Image, ImageEnhance


def apply_watermark(
    im: Image.Image,
    watermark_path: Union[str, Path],
    position: str = "Bottom Right",
    scale_ratio: float = 0.20,
    opacity: float = 0.75,
    margin_x: int = 15,
    margin_y: int = 15,
    target_format: str = "WEBP"
) -> Image.Image:
    """
    Applies a watermark to the image with boundary clamping and auto-scaling.
    Safely clamps coordinates to prevent negative or out-of-bounds positioning.
    Scales watermark proportionally if it exceeds the base image boundaries.
    """
    if not watermark_path:
        return im

    wm_path = Path(watermark_path)
    if not wm_path.exists() or not wm_path.is_file():
        return im

    img_w, img_h = im.size
    if img_w <= 0 or img_h <= 0:
        return im

    orig_mode = im.mode

    try:
        with Image.open(wm_path) as raw_wm:
            wm = raw_wm.convert("RGBA")
    except Exception:
        return im

    wm_w, wm_h = wm.size
    if wm_w <= 0 or wm_h <= 0:
        return im

    # Calculate target width based on scale_ratio of base image width
    target_w = max(1, int(img_w * scale_ratio))
    aspect = target_w / float(wm_w)
    target_h = max(1, int(wm_h * aspect))

    # Auto-scale down if watermark exceeds base image dimensions
    if target_w > img_w or target_h > img_h:
        scale_down = min(img_w / float(target_w), img_h / float(target_h))
        target_w = max(1, int(target_w * scale_down))
        target_h = max(1, int(target_h * scale_down))

    wm = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Opacity adjustment
    clamped_opacity = max(0.0, min(1.0, float(opacity)))
    if clamped_opacity < 1.0:
        r, g, b, a = wm.split()
        a = ImageEnhance.Brightness(a).enhance(clamped_opacity)
        wm.putalpha(a)

    # Margins clamping
    mx = max(0, min(margin_x, max(0, img_w - target_w)))
    my = max(0, min(margin_y, max(0, img_h - target_h)))

    # Position computation
    pos_lower = str(position).strip().lower()
    if pos_lower == "top left":
        x = mx
        y = my
    elif pos_lower == "top right":
        x = img_w - target_w - mx
        y = my
    elif pos_lower == "bottom left":
        x = mx
        y = img_h - target_h - my
    elif pos_lower == "center":
        x = (img_w - target_w) // 2
        y = (img_h - target_h) // 2
    else:  # Default: Bottom Right
        x = img_w - target_w - mx
        y = img_h - target_h - my

    # Safe coordinate clamping
    x = max(0, min(x, img_w - target_w))
    y = max(0, min(y, img_h - target_h))

    # Composite onto image
    if im.mode != "RGBA":
        im_rgba = im.convert("RGBA")
    else:
        im_rgba = im.copy()

    overlay = Image.new("RGBA", im_rgba.size, (0, 0, 0, 0))
    overlay.paste(wm, (x, y))
    composited = Image.alpha_composite(im_rgba, overlay)

    # Restore appropriate color mode for format
    fmt_upper = str(target_format).upper()
    if orig_mode == "L":
        return composited.convert("L")
    elif fmt_upper in ("JPEG", "JPG"):
        # JPEG does not support alpha; composite over white background
        bg = Image.new("RGB", composited.size, (255, 255, 255))
        bg.paste(composited, mask=composited.split()[-1])
        return bg
    elif fmt_upper == "BMP":
        return composited.convert("RGB")
    else:
        return composited
