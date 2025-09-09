"""
A simple pytest for converter: convert a PNG sample to JPG and assert output exists.
"""
from pathlib import Path
from formato import converter
from formato.utils import ensure_output_folder

def test_convert_sample(tmp_path):
    assets = Path(__file__).parent.parent / "assets" / "sample_images"
    src = assets / "sample1.png"
    assert src.exists(), "Sample image missing"
    out = tmp_path / "out.jpg"
    res = converter.convert_image(src, out, fmt="JPEG", quality=80, preserve_exif=True)
    assert res["success"], f"Conversion failed: {res.get('error')}"
    assert out.exists()
