import unittest
import tempfile
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image
from core.watermark import apply_watermark


class TestWatermark(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Base image: 300x200
        self.base_img = Image.new("RGB", (300, 200), (50, 100, 150))

        # Normal watermark: 50x50 PNG
        self.wm_path = self.dir_path / "wm.png"
        wm_img = Image.new("RGBA", (50, 50), (255, 255, 255, 200))
        wm_img.save(self.wm_path)

        # Oversized watermark: 800x800 PNG (much larger than base image)
        self.large_wm_path = self.dir_path / "huge_wm.png"
        huge_wm = Image.new("RGBA", (800, 800), (255, 255, 0, 180))
        huge_wm.save(self.large_wm_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_watermark_positions(self):
        positions = ["Bottom Right", "Bottom Left", "Top Right", "Top Left", "Center"]
        for pos in positions:
            res = apply_watermark(
                im=self.base_img,
                watermark_path=self.wm_path,
                position=pos,
                scale_ratio=0.2,
                opacity=0.8
            )
            self.assertEqual(res.size, (300, 200))

    def test_oversized_watermark_auto_scaled_safely(self):
        # Even with an 800x800 watermark on a 300x200 image, it shouldn't crash
        # and coordinates must remain bounded
        res = apply_watermark(
            im=self.base_img,
            watermark_path=self.large_wm_path,
            position="Bottom Right",
            scale_ratio=0.5,
            margin_x=10,
            margin_y=10
        )
        self.assertEqual(res.size, (300, 200))

    def test_watermark_pipeline_integration(self):
        out_p = self.dir_path / "wm_out.webp"
        settings = ConversionSettings(
            fmt="WEBP",
            wm=str(self.wm_path),
            wm_pos="Top Left",
            wm_size=0.15,
            wm_opacity=0.5
        )
        res = process_image(self.base_img, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())


if __name__ == "__main__":
    unittest.main()
