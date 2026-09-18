import unittest
import tempfile
import threading
from pathlib import Path
from PIL import Image
from models.conversion_settings import ConversionSettings
from core.pipeline import process_image


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        self.src_path = self.dir_path / "test_pipe.png"
        Image.new("RGB", (400, 300), (80, 120, 160)).save(self.src_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_preview_mode_does_not_touch_disk(self):
        settings = ConversionSettings(
            fmt="JPEG",
            adj_b=1.2,
            adj_c=1.1,
            f_auto=True
        )
        res = process_image(self.src_path, settings, output_path=None, preview=True)
        self.assertTrue(res.success)
        self.assertIsNotNone(res.preview_image)
        self.assertIsNone(res.output_path)

    def test_pipeline_cancellation(self):
        out_p = self.dir_path / "cancel_test.webp"
        cancel_evt = threading.Event()
        cancel_evt.set()

        settings = ConversionSettings(fmt="WEBP")
        res = process_image(self.src_path, settings, output_path=out_p, cancel_event=cancel_evt)
        self.assertFalse(res.success)
        self.assertTrue(res.was_cancelled)
        self.assertFalse(out_p.exists())

    def test_full_pipeline_combination(self):
        out_p = self.dir_path / "full_features.webp"
        settings = ConversionSettings(
            fmt="WEBP",
            qual=85,
            res_w_str="200",
            res_h_str="150",
            mode="Fit (Maintain AR)",
            adj_b=1.1,
            adj_c=1.1,
            adj_s=0.9,
            adj_sh=1.2,
            f_auto=True,
            f_edge=True,
            meta_en=True,
            meta_auth="Formato Tester"
        )
        res = process_image(self.src_path, settings, output_path=out_p)
        self.assertTrue(res.success)
        self.assertTrue(out_p.exists())
        self.assertGreater(res.actual_size_bytes, 0)


if __name__ == "__main__":
    unittest.main()
