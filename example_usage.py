"""
Example usage of converter module (non-GUI).
Converts sample images in assets/sample_images to JPEG into formato_output_example/.
"""
from formato import converter
from pathlib import Path
from formato.utils import ensure_output_folder

src_dir = Path(__file__).parent / "assets" / "sample_images"
out = Path(__file__).parent / "example_output"
ensure_output_folder(out)

for p in src_dir.iterdir():
    if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
        dest = out / (p.stem + ".jpg")
        res = converter.convert_image(p, dest, fmt="JPEG", quality=85, preserve_exif=True)
        print(p.name, "->", dest.name, ":", res)
