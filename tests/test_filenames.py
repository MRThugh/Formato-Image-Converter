import unittest
import tempfile
from pathlib import Path
from utils.filenames import get_unique_output_path


class TestFilenames(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_unicode_and_persian_filenames(self):
        names = [
            "عکس من",
            "تصویر تست شماره ۱",
            "صورة_تجريبية",
            "My Image with spaces and special @#",
            "日本語の画像"
        ]
        for name in names:
            p = get_unique_output_path(self.dir_path, name, "webp")
            self.assertTrue(p.name.startswith(name))
            self.assertEqual(p.suffix, ".webp")

    def test_filename_collision_avoidance_on_disk(self):
        # Create an existing file
        existing = self.dir_path / "photo.jpg"
        existing.touch()

        # Requesting photo.jpg again should yield photo_1.jpg
        p1 = get_unique_output_path(self.dir_path, "photo", "jpg")
        self.assertEqual(p1.name, "photo_1.jpg")
        p1.touch()

        # Requesting a third time should yield photo_2.jpg
        p2 = get_unique_output_path(self.dir_path, "photo", "jpg")
        self.assertEqual(p2.name, "photo_2.jpg")

    def test_reserved_paths_concurrency(self):
        # Simulating concurrent workers reserving output paths before writing to disk
        reserved = set()
        p1 = get_unique_output_path(self.dir_path, "batch_item", "png", reserved_paths=reserved)
        p2 = get_unique_output_path(self.dir_path, "batch_item", "png", reserved_paths=reserved)
        p3 = get_unique_output_path(self.dir_path, "batch_item", "png", reserved_paths=reserved)

        self.assertEqual(p1.name, "batch_item.png")
        self.assertEqual(p2.name, "batch_item_1.png")
        self.assertEqual(p3.name, "batch_item_2.png")
        self.assertEqual(len(reserved), 3)


if __name__ == "__main__":
    unittest.main()
