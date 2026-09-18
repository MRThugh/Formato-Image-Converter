import unittest
import tempfile
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image


class TestFormatConversions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Source RGBA image with transparency
        self.rgba_img_path = self.dir_path / "sample_rgba.png"
        img = Image.new("RGBA", (150, 150), (255, 0, 0, 128))
        img.save(self.rgba_img_path)

        # Corrupt file
        self.corrupt_path = self.dir_path / "corrupted.jpg"
        with open(self.corrupt_path, "wb") as f:
            f.write(b"NOT_AN_IMAGE_DATA_CORRUPT_HEADER")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_convert_to_jpeg_flatten_transparency(self):
        out_p = self.dir_path / "out.jpg"
        settings = ConversionSettings(fmt="JPEG", qual=90)
        res = process_image(self.rgba_img_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        with Image.open(out_p) as check_img:
            self.assertEqual(check_img.format, "JPEG")
            self.assertEqual(check_img.mode, "RGB")

    def test_convert_to_webp(self):
        out_p = self.dir_path / "out.webp"
        settings = ConversionSettings(fmt="WEBP", qual=80)
        res = process_image(self.rgba_img_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        with Image.open(out_p) as check_img:
            self.assertEqual(check_img.format, "WEBP")

    def test_convert_to_png(self):
        out_p = self.dir_path / "out.png"
        settings = ConversionSettings(fmt="PNG")
        res = process_image(self.rgba_img_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        with Image.open(out_p) as check_img:
            self.assertEqual(check_img.format, "PNG")

    def test_convert_to_bmp(self):
        out_p = self.dir_path / "out.bmp"
        settings = ConversionSettings(fmt="BMP")
        res = process_image(self.rgba_img_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        with Image.open(out_p) as check_img:
            self.assertEqual(check_img.format, "BMP")

    def test_convert_to_tiff(self):
        out_p = self.dir_path / "out.tiff"
        settings = ConversionSettings(fmt="TIFF")
        res = process_image(self.rgba_img_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        with Image.open(out_p) as check_img:
            self.assertEqual(check_img.format, "TIFF")

    def test_corrupt_image_graceful_failure(self):
        out_p = self.dir_path / "corrupt_out.webp"
        settings = ConversionSettings(fmt="WEBP")
        res = process_image(self.corrupt_path, settings, output_path=out_p)
        self.assertFalse(res.success)
        self.assertTrue(len(res.error_msg) > 0)
        self.assertFalse(out_p.exists())


if __name__ == "__main__":
    unittest.main()
