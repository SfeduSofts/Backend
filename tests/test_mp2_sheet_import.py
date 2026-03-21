import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.mp2_sheet_import import parse_projects_sheet


class ParseProjectsSheetTests(unittest.TestCase):
    @patch("app.services.mp2_sheet_import._load_csv_rows")
    def test_parses_pdf_and_image_links_from_rows_before_team_header(self, mock_load_csv_rows):
        mock_load_csv_rows.return_value = [
            ["Второй междисциплинарный проект 2025"],
            ["Наставник", "Болдырев Санал Бадмаевич", ""],
            ["Категория", "Сетевые технологии", "Аналитика"],
            ["Тема", "Квантовая сеть для передачи данных", "Project metrA"],
            ["Аудитория", "a-101", "b-202"],
            ["PDF", "https://example.com/quantum.pdf", ""],
            ["Фото", "https://example.com/quantum.jpg", "https://example.com/metra.png"],
            ["Название команды", "SfeduSoft", "Project metrA"],
            ["1", "Иванов Иван", "Петров Петр"],
        ]

        parsed = parse_projects_sheet(
            "https://docs.google.com/spreadsheets/d/test-sheet-id/edit?gid=123#gid=123"
        )
        projects_by_name = {project["name"]: project for project in parsed["projects"]}

        self.assertEqual(
            projects_by_name["Квантовая сеть для передачи данных"]["pdf_url"],
            "https://example.com/quantum.pdf",
        )
        self.assertEqual(
            projects_by_name["Квантовая сеть для передачи данных"]["image_url"],
            "https://example.com/quantum.jpg",
        )
        self.assertEqual(projects_by_name["Project metrA"]["pdf_url"], "")
        self.assertEqual(
            projects_by_name["Project metrA"]["image_url"],
            "https://example.com/metra.png",
        )


if __name__ == "__main__":
    unittest.main()
