import unittest
import tempfile
import threading
from pathlib import Path
from PIL import Image
from core.pdf_builder import build_pdf_from_images


class TestPdfBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create 3 test images
        self.images = []
        for i in range(3):
            p = self.dir_path / f"img_{i}.png"
            Image.new("RGB", (300 + i * 50, 400), (50 * i, 70 * i, 100)).save(p)
            self.images.append(p)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_pdf_success(self):
        out_pdf = self.dir_path / "output.pdf"
        ok, msg = build_pdf_from_images(
            image_paths=self.images,
            output_pdf_path=out_pdf,
            page_size_name="A4",
            orientation="Portrait",
            fit_mode="Fit",
            margin=15
        )
        self.assertTrue(ok)
        self.assertTrue(out_pdf.exists())
        self.assertGreater(out_pdf.stat().st_size, 0)

    def test_build_pdf_cancellation(self):
        out_pdf = self.dir_path / "cancelled.pdf"
        cancel_evt = threading.Event()
        cancel_evt.set()  # Pre-cancelled

        ok, msg = build_pdf_from_images(
            image_paths=self.images,
            output_pdf_path=out_pdf,
            cancel_event=cancel_evt
        )
        self.assertFalse(ok)
        self.assertIn("cancelled", msg.lower())
        self.assertFalse(out_pdf.exists())


if __name__ == "__main__":
    unittest.main()
