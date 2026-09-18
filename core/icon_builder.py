from pathlib import Path
from typing import List, Tuple, Union
from PIL import Image, ImageOps
from utils.filenames import get_temp_output_path


def generate_ico(
    source_path: Union[str, Path],
    output_ico_path: Union[str, Path],
    sizes: List[int] = [16, 32, 48, 64, 128, 256]
) -> Tuple[bool, str]:
    """
    Generates a Windows .ico icon file containing multiple embedded resolutions.
    """
    src = Path(source_path)
    if not src.exists():
        return False, f"Source image does not exist: {src}"

    out_p = Path(output_ico_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_p = get_temp_output_path(out_p)

    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            icon_sizes = [(s, s) for s in sizes if 16 <= s <= 256]
            if not icon_sizes:
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

            img.save(temp_p, format="ICO", sizes=icon_sizes)

        temp_p.replace(out_p)
        return True, "ICO generated successfully"
    except Exception as e:
        if temp_p.exists():
            try:
                temp_p.unlink()
            except Exception:
                pass
        return False, str(e)
