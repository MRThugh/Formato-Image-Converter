import unittest
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image
from utils.helpers import get_resize_dimensions


class TestResize(unittest.TestCase):
    def setUp(self):
        # 200x100 RGB image (2:1 aspect ratio)
        self.img = Image.new("RGB", (200, 100), color=(100, 150, 200))

    def test_dimension_helper_proportional_width(self):
        dim = get_resize_dimensions((200, 100), "100", "")
        self.assertEqual(dim, (100, 50))

    def test_dimension_helper_proportional_height(self):
        dim = get_resize_dimensions((200, 100), "", "50")
        self.assertEqual(dim, (100, 50))

    def test_dimension_helper_both(self):
        dim = get_resize_dimensions((200, 100), "300", "400")
        self.assertEqual(dim, (300, 400))

    def test_resize_stretch(self):
        settings = ConversionSettings(
            fmt="PNG",
            mode="Stretch",
            res_w_str="120",
            res_h_str="80"
        )
        res = process_image(self.img, settings, preview=True)
        self.assertTrue(res.success)
        self.assertEqual(res.preview_image.size, (120, 80))

    def test_resize_fit_maintains_aspect_ratio(self):
        # Base image is 200x100 (2:1). Fit inside 100x100 bounding box => 100x50
        settings = ConversionSettings(
            fmt="PNG",
            mode="Fit (Maintain AR)",
            res_w_str="100",
            res_h_str="100"
        )
        res = process_image(self.img, settings, preview=True)
        self.assertTrue(res.success)
        self.assertEqual(res.preview_image.size, (100, 50))

    def test_resize_fill_crop_exact_box(self):
        # Fill/Crop into 100x100 should crop edges to achieve exactly 100x100
        settings = ConversionSettings(
            fmt="PNG",
            mode="Fill/Crop",
            res_w_str="100",
            res_h_str="100"
        )
        res = process_image(self.img, settings, preview=True)
        self.assertTrue(res.success)
        self.assertEqual(res.preview_image.size, (100, 100))


if __name__ == "__main__":
    unittest.main()
