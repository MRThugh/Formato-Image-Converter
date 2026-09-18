from typing import Optional, Tuple


def parse_int(val, default: int = 10) -> int:
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def parse_float(val, default: float = 1.0) -> float:
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    else:
        return f"{num_bytes / (1024 * 1024):.2f} MB"


def get_resize_dimensions(im_size: Tuple[int, int], w_str: str, h_str: str) -> Optional[Tuple[int, int]]:
    """
    Calculates target width and height.
    If only width is given, height is scaled proportionally.
    If only height is given, width is scaled proportionally.
    """
    w_clean = str(w_str).strip() if w_str else ""
    h_clean = str(h_str).strip() if h_str else ""

    w = int(w_clean) if w_clean.isdigit() and int(w_clean) > 0 else None
    h = int(h_clean) if h_clean.isdigit() and int(h_clean) > 0 else None
    orig_w, orig_h = im_size

    if orig_w <= 0 or orig_h <= 0:
        return None

    if w and not h:
        h = max(1, int(orig_h * (w / float(orig_w))))
    elif h and not w:
        w = max(1, int(orig_w * (h / float(orig_h))))

    if w and h:
        return (w, h)
    return None
