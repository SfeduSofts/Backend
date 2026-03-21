import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["debug"] = "false"

from app.services.project_service import ProjectService


class ProjectServiceHelperTests(unittest.TestCase):
    def setUp(self):
        self.service = ProjectService.__new__(ProjectService)

    def test_normalizes_google_drive_file_links_to_direct_download(self):
        source_url = "https://drive.google.com/file/d/abc123_DEF-45/view?usp=drive_link"

        normalized_url = self.service._normalize_remote_file_url(source_url)

        self.assertEqual(
            normalized_url,
            "https://drive.google.com/uc?export=download&id=abc123_DEF-45",
        )

    def test_save_image_bytes_replaces_previous_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            static_dir = Path(temp_dir)
            old_image_path = static_dir / "7.jpeg"
            old_image_path.write_bytes(b"\xff\xd8\xffold")

            with patch.object(self.service, "_get_static_dir", return_value=static_dir):
                self.service._save_image_bytes(7, b"\x89PNG\r\n\x1a\nnew", "image/png")

            self.assertFalse(old_image_path.exists())
            self.assertEqual((static_dir / "7.png").read_bytes(), b"\x89PNG\r\n\x1a\nnew")


if __name__ == "__main__":
    unittest.main()
