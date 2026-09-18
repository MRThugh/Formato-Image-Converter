import unittest
import tempfile
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image


class TestGif(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create multi-frame animated GIF
        self.gif_path = self.dir_path / "animated.gif"
        frames = [
            Image.new("RGB", (60, 60), color=(255, 0, 0)),
            Image.new("RGB", (60, 60), color=(0, 255, 0)),
            Image.new("RGB", (60, 60), color=(0, 0, 255)),
        ]
        frames[0].save(
            self.gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_animated_gif_preserves_frames(self):
        out_p = self.dir_path / "out_anim.gif"
        settings = ConversionSettings(fmt="GIF")
        res = process_image(self.gif_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())

        with Image.open(out_p) as check_img:
            self.assertTrue(getattr(check_img, "is_animated", False))
            self.assertEqual(check_img.n_frames, 3)

    def test_convert_static_png_to_gif(self):
        png_path = self.dir_path / "static.png"
        Image.new("RGBA", (80, 80), (100, 200, 50, 255)).save(png_path)

        out_p = self.dir_path / "from_static.gif"
        settings = ConversionSettings(fmt="GIF")
        res = process_image(png_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())


if __name__ == "__main__":
    unittest.main()
