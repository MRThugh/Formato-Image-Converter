import unittest
import tempfile
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image


class TestMetadata(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        self.src_path = self.dir_path / "meta_test.jpg"
        img = Image.new("RGB", (100, 100), (200, 100, 50))
        img.save(self.src_path, format="JPEG")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_custom_metadata_injection(self):
        out_p = self.dir_path / "custom_meta.jpg"
        settings = ConversionSettings(
            fmt="JPEG",
            meta_en=True,
            meta_auth="Ali Kamrani",
            meta_copy="2026 Formato",
            meta_desc="Sample Description"
        )
        res = process_image(self.src_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())

        with Image.open(out_p) as check_img:
            exif = check_img.getexif()
            self.assertEqual(exif.get(315), "Ali Kamrani")
            self.assertEqual(exif.get(33432), "2026 Formato")
            self.assertEqual(exif.get(270), "Sample Description")

    def test_strip_metadata(self):
        out_p = self.dir_path / "stripped.jpg"
        settings = ConversionSettings(
            fmt="JPEG",
            exif=False,
            meta_en=False
        )
        res = process_image(self.src_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())


if __name__ == "__main__":
    unittest.main()
