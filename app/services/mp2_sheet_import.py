import csv
import io
import re
from datetime import datetime
from typing import Any
from urllib.request import urlopen


MP2_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1R0BEkbBeJ9TB2UFpu33EuP_2w0WAN0xGAchzvzFG8EI/export"
    "?format=csv&gid=1622739093"
)


def parse_mp2_sheet(url: str = MP2_SHEET_CSV_URL) -> dict[str, Any]:
    rows = _load_csv_rows(url)
    if not rows:
        return {"projects": [], "year": datetime.now().year}

    topic_row_index = _find_row_index(rows, "Тема")
    if topic_row_index is None:
        return {"projects": [], "year": datetime.now().year}

    teacher_row_index = _find_row_index(rows, "Наставник")
    mentor_row_index = _find_row_index(rows, "Ментор")
    team_header_rows = _find_all_row_indices(rows, "Название команды")
    import_year = _extract_start_year(rows)

    max_cols = max((len(row) for row in rows), default=0)
    projects_by_key: dict[str, dict[str, Any]] = {}

    for col_index in range(1, max_cols):
        project_name = _cell(rows, topic_row_index, col_index)
        project_name = _normalize_spaces(project_name)
        if not _is_project_name_valid(project_name):
            continue

        category = _cell(rows, max(topic_row_index - 1, 0), col_index)
        category = _normalize_spaces(category)
        mentor = _pick_mentor(rows, teacher_row_index, mentor_row_index, col_index)
        teams = _collect_teams_for_column(rows, team_header_rows, col_index)

        key = _normalize_key(project_name)
        if key not in projects_by_key:
            projects_by_key[key] = {
                "name": project_name,
                "mentor": mentor,
                "description": _build_short_description(project_name, category),
                "full_description": _build_full_description(project_name, category),
                "teams": {},
            }

        project_entry = projects_by_key[key]
        if not project_entry.get("mentor") and mentor:
            project_entry["mentor"] = mentor

        for team in teams:
            team_name = _normalize_spaces(team["name"])
            if not team_name:
                continue
            existing_students = project_entry["teams"].setdefault(team_name, [])
            existing_keys = {_normalize_key(student["name"]) for student in existing_students}

            for student in team["students"]:
                student_name = _normalize_spaces(student["name"])
                if not student_name:
                    continue
                student_key = _normalize_key(student_name)
                if student_key in existing_keys:
                    continue
                existing_students.append({"name": student_name, "role": ""})
                existing_keys.add(student_key)

    projects = []
    for project in projects_by_key.values():
        teams_list = [
            {"name": team_name, "students": students}
            for team_name, students in project["teams"].items()
        ]
        projects.append(
            {
                "name": project["name"],
                "mentor": project["mentor"],
                "description": project["description"],
                "full_description": project["full_description"],
                "year": import_year,
                "type": "МП2",
                "teams": teams_list,
            }
        )

    return {"projects": projects, "year": import_year}


def _load_csv_rows(url: str) -> list[list[str]]:
    with urlopen(url, timeout=30) as response:
        payload = response.read()

    decoded = _decode_payload(payload)
    reader = csv.reader(io.StringIO(decoded))

    result: list[list[str]] = []
    for row in reader:
        result.append([_fix_mojibake(cell) for cell in row])
    return result


def _decode_payload(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _fix_mojibake(text: str) -> str:
    value = str(text or "").replace("\ufeff", "").replace("\r", "\n")
    if "Ð" in value or "Ñ" in value or "Â" in value:
        try:
            value = value.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    return value.strip()


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _normalize_key(text: str) -> str:
    return _normalize_spaces(text).lower()


def _find_row_index(rows: list[list[str]], label: str) -> int | None:
    target = _normalize_key(label)
    for index, row in enumerate(rows):
        if _normalize_key(_cell(rows, index, 0)) == target:
            return index
    return None


def _find_all_row_indices(rows: list[list[str]], label: str) -> list[int]:
    target = _normalize_key(label)
    result: list[int] = []
    for index, _ in enumerate(rows):
        if _normalize_key(_cell(rows, index, 0)) == target:
            result.append(index)
    return result


def _cell(rows: list[list[str]], row_index: int, col_index: int) -> str:
    if row_index < 0 or row_index >= len(rows):
        return ""
    row = rows[row_index]
    if col_index < 0 or col_index >= len(row):
        return ""
    return str(row[col_index] or "").strip()


def _extract_start_year(rows: list[list[str]]) -> int:
    probe = " ".join(" ".join(row[:3]) for row in rows[:3])
    match = re.search(r"(20\d{2})", _fix_mojibake(probe))
    if match:
        year = int(match.group(1))
        if 2016 <= year <= 2100:
            return year
    return datetime.now().year


def _pick_mentor(
    rows: list[list[str]],
    teacher_row_index: int | None,
    mentor_row_index: int | None,
    col_index: int,
) -> str:
    teacher = _normalize_spaces(_cell(rows, teacher_row_index, col_index)) if teacher_row_index is not None else ""
    mentor = _normalize_spaces(_cell(rows, mentor_row_index, col_index)) if mentor_row_index is not None else ""
    source = teacher or mentor
    source = re.sub(r"\b(Наставник ИУЭС|Наставник|Ментор)\s*:\s*", "", source, flags=re.IGNORECASE)
    source = _normalize_spaces(source)
    return source[:100]


def _build_short_description(project_name: str, category: str) -> str:
    base = category if len(category) >= 3 else f"Проект МП2: {project_name}"
    return base[:1000]


def _build_full_description(project_name: str, category: str) -> str:
    if category:
        return f"{project_name}. Категория: {category}"[:1000]
    return project_name[:1000]


def _is_project_name_valid(project_name: str) -> bool:
    if not project_name:
        return False
    if re.fullmatch(r"\d+", project_name):
        return False
    return len(project_name) >= 3


def _collect_teams_for_column(
    rows: list[list[str]],
    team_header_rows: list[int],
    col_index: int,
) -> list[dict[str, Any]]:
    teams: list[dict[str, Any]] = []
    if not team_header_rows:
        return teams

    for block_index, header_row in enumerate(team_header_rows):
        next_header = (
            team_header_rows[block_index + 1]
            if block_index + 1 < len(team_header_rows)
            else len(rows)
        )
        team_name = _normalize_spaces(_cell(rows, header_row, col_index))
        if not team_name:
            continue

        students: list[dict[str, str]] = []
        for row_index in range(header_row + 1, next_header):
            label = _normalize_spaces(_cell(rows, row_index, 0))
            raw_student = _normalize_spaces(_cell(rows, row_index, col_index))
            if not raw_student:
                continue

            if label and not re.fullmatch(r"\d+", label):
                continue

            if not _looks_like_student(raw_student):
                continue

            student_name = _clean_student_name(raw_student)
            if student_name:
                students.append({"name": student_name, "role": ""})

        teams.append({"name": team_name, "students": students})

    return teams


def _looks_like_student(raw_value: str) -> bool:
    value = _normalize_spaces(raw_value)
    if not value:
        return False
    if value.upper() in {"X", "Х"}:
        return False
    if "@" in value:
        return False
    if re.fullmatch(r"n\d+", value, flags=re.IGNORECASE):
        return False

    words = re.split(r"\s+", value)
    if len(words) < 2:
        return False

    letters_count = sum(char.isalpha() for char in value)
    return letters_count >= 6


def _clean_student_name(raw_value: str) -> str:
    value = _normalize_spaces(raw_value.replace("\n", " "))
    tokens = value.split()
    while tokens and (re.search(r"\d", tokens[-1]) or tokens[-1].startswith("(") or tokens[-1].endswith(")")):
        tokens.pop()

    cleaned = " ".join(tokens).strip()
    return cleaned or value
