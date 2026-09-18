import unittest
import tempfile
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image


class TestCompression(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create a detailed test image (gradients and patterns compress differently with quality)
        self.test_img_path = self.dir_path / "compress_sample.png"
        img = Image.new("RGB", (600, 600))
        pixels = img.load()
        for x in range(600):
            for y in range(600):
                pixels[x, y] = (x % 256, y % 256, (x * y) % 256)
        img.save(self.test_img_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_quality_impact(self):
        # Higher quality should result in larger file size than low quality
        out_low = self.dir_path / "low.jpg"
        out_high = self.dir_path / "high.jpg"

        s_low = ConversionSettings(fmt="JPEG", qual=20)
        s_high = ConversionSettings(fmt="JPEG", qual=95)

        res_low = process_image(self.test_img_path, s_low, output_path=out_low)
        res_high = process_image(self.test_img_path, s_high, output_path=out_high)

        self.assertTrue(res_low.success)
        self.assertTrue(res_high.success)
        self.assertLess(out_low.stat().st_size, out_high.stat().st_size)

    def test_smart_compression_target_achievable(self):
        out_smart = self.dir_path / "smart.jpg"
        # Request target size 40 KB
        s_smart = ConversionSettings(fmt="JPEG", smart=True, target_kb=40)
        res = process_image(self.test_img_path, s_smart, output_path=out_smart)

        self.assertTrue(res.success)
        # Verify output exists and is close to target
        self.assertTrue(out_smart.exists())
        self.assertLessEqual(out_smart.stat().st_size, 45 * 1024)

    def test_smart_compression_target_unreachable_reports_honestly(self):
        out_smart = self.dir_path / "unreachable.jpg"
        # Request an impossible target size: 1 KB for 600x600 high entropy image
        s_smart = ConversionSettings(fmt="JPEG", smart=True, target_kb=1)
        res = process_image(self.test_img_path, s_smart, output_path=out_smart)

        self.assertTrue(res.success)
        self.assertFalse(res.target_size_achieved)
        self.assertEqual(res.final_quality, 10)


if __name__ == "__main__":
    unittest.main()
