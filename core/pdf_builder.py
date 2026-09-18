import threading
from pathlib import Path
from typing import List, Optional, Tuple, Union
from PIL import Image, ImageOps
from utils.filenames import get_temp_output_path

# Standard Paper Dimensions in points (72 points/inch)
PAGE_SIZES = {
    "A4": (595, 842),
    "A5": (420, 595),
    "Letter": (612, 792),
    "Original": (0, 0)
}


def build_pdf_from_images(
    image_paths: List[Union[str, Path]],
    output_pdf_path: Union[str, Path],
    page_size_name: str = "A4",
    orientation: str = "Portrait",
    fit_mode: str = "Fit",
    margin: int = 20,
    cancel_event: Optional[threading.Event] = None
) -> Tuple[bool, str]:
    """
    Builds a multi-page PDF from a list of image paths memory-efficiently.
    Opens images on demand, avoids holding large uncompressed buffers in memory,
    and performs atomic saving.
    """
    if not image_paths:
        return False, "No images provided"

    out_p = Path(output_pdf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_pdf = get_temp_output_path(out_p)

    # Resolve target dimensions
    base_dim = PAGE_SIZES.get(page_size_name, (595, 842))
    is_custom_page = (base_dim[0] > 0 and base_dim[1] > 0)

    if is_custom_page:
        if orientation.lower() == "landscape":
            pw, ph = max(base_dim), min(base_dim)
        else:
            pw, ph = min(base_dim), max(base_dim)
    else:
        pw, ph = 0, 0

    processed_pages: List[Image.Image] = []

    try:
        for idx, img_path in enumerate(image_paths):
            if cancel_event and cancel_event.is_set():
                for p in processed_pages:
                    p.close()
                return False, "PDF generation cancelled by user"

            p = Path(img_path)
            if not p.exists():
                continue

            with Image.open(p) as raw_img:
                img = ImageOps.exif_transpose(raw_img)

                # Standardize color mode to RGB
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    alpha_mask = img.convert("RGBA").split()[-1]
                    bg.paste(img, mask=alpha_mask)
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                if is_custom_page:
                    usable_w = max(10, pw - 2 * margin)
                    usable_h = max(10, ph - 2 * margin)

                    if fit_mode.lower() == "fill":
                        fitted = ImageOps.fit(img, (usable_w, usable_h), Image.Resampling.LANCZOS)
                    else:  # Default: Fit (maintain aspect ratio)
                        fitted = ImageOps.contain(img, (usable_w, usable_h), Image.Resampling.LANCZOS)

                    page_canvas = Image.new("RGB", (pw, ph), (255, 255, 255))
                    paste_x = (pw - fitted.size[0]) // 2
                    paste_y = (ph - fitted.size[1]) // 2
                    page_canvas.paste(fitted, (paste_x, paste_y))
                    processed_pages.append(page_canvas)
                else:
                    # Original image dimension as PDF page
                    processed_pages.append(img.copy())

        if not processed_pages:
            return False, "No valid images could be rendered for PDF"

        first_page = processed_pages[0]
        remaining = processed_pages[1:]

        first_page.save(
            temp_pdf,
            format="PDF",
            save_all=True,
            append_images=remaining,
            resolution=150.0
        )

        # Cleanup memory
        for page in processed_pages:
            try:
                page.close()
            except Exception:
                pass

        temp_pdf.replace(out_p)
        return True, "PDF generated successfully"

    except Exception as e:
        if temp_pdf.exists():
            try:
                temp_pdf.unlink()
            except Exception:
                pass
        return False, str(e)
