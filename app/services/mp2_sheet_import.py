import csv
import io
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen


PROJECT_TYPE_MP1 = "МП1"
PROJECT_TYPE_MP2 = "МП2"

DEFAULT_MP2_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1R0BEkbBeJ9TB2UFpu33EuP_2w0WAN0xGAchzvzFG8EI/edit"
    "?gid=1622739093#gid=1622739093"
)


def parse_projects_sheet(url: str = DEFAULT_MP2_SHEET_URL) -> dict[str, Any]:
    csv_url = _build_csv_export_url(url)
    rows = _load_csv_rows(csv_url)
    if not rows:
        return {
            "projects": [],
            "year": datetime.now().year,
            "type": PROJECT_TYPE_MP2,
            "source_url": csv_url,
            "header": "",
        }

    header_text = _extract_header_text(rows)
    detected_type = _detect_project_type(header_text)
    import_year = _extract_start_year(rows, header_text)

    topic_row_index = _find_row_index(rows, ("Тема", "Тема проекта", "Название проекта"))
    if topic_row_index is None:
        return {
            "projects": [],
            "year": import_year,
            "type": detected_type,
            "source_url": csv_url,
            "header": header_text,
        }

    teacher_row_index = _find_row_index(
        rows,
        ("Наставник", "Преподаватель", "Руководитель", "Научный руководитель"),
    )
    mentor_row_index = _find_row_index(rows, ("Ментор",))
    team_header_rows = _find_all_row_indices(rows, ("Название команды", "Команда"))

    max_cols = max((len(row) for row in rows), default=0)
    projects_by_key: dict[str, dict[str, Any]] = {}

    for col_index in range(1, max_cols):
        project_name = _normalize_spaces(_cell(rows, topic_row_index, col_index))
        if not _is_project_name_valid(project_name):
            continue

        category = _normalize_spaces(_cell(rows, max(topic_row_index - 1, 0), col_index))
        mentor = _pick_mentor(rows, teacher_row_index, mentor_row_index, col_index)
        teams = _collect_teams_for_column(rows, team_header_rows, col_index)

        key = _normalize_key(project_name)
        if key not in projects_by_key:
            projects_by_key[key] = {
                "name": project_name,
                "mentor": mentor,
                "description": _build_short_description(project_name, category, detected_type),
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
                "type": detected_type,
                "teams": teams_list,
            }
        )

    return {
        "projects": projects,
        "year": import_year,
        "type": detected_type,
        "source_url": csv_url,
        "header": header_text,
    }


def parse_mp2_sheet(url: str = DEFAULT_MP2_SHEET_URL) -> dict[str, Any]:
    return parse_projects_sheet(url)


def _build_csv_export_url(url: str) -> str:
    source_url = str(url or "").strip()
    if not source_url:
        source_url = DEFAULT_MP2_SHEET_URL

    sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", source_url)
    if not sheet_match:
        raise ValueError("Unsupported Google Sheets URL format")

    sheet_id = sheet_match.group(1)
    gid = _extract_gid(source_url)

    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if gid is not None:
        export_url += f"&gid={gid}"
    return export_url


def _extract_gid(url: str) -> int | None:
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    if "gid" in query and query["gid"]:
        return _safe_gid(query["gid"][0])

    fragment = parse_qs(parts.fragment)
    if "gid" in fragment and fragment["gid"]:
        return _safe_gid(fragment["gid"][0])

    match = re.search(r"gid=(\d+)", url)
    if match:
        return _safe_gid(match.group(1))
    return None


def _safe_gid(value: str) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if not raw.isdigit():
        return None
    return int(raw)


def _load_csv_rows(url: str) -> list[list[str]]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
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
    if "Гђ" in value or "Г‘" in value or "Г‚" in value:
        try:
            value = value.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    return value.strip()


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _normalize_key(text: str) -> str:
    return _normalize_spaces(text).replace("ё", "е").lower()


def _normalize_label(text: str) -> str:
    return _normalize_key(str(text or "").replace(":", ""))


def _extract_header_text(rows: list[list[str]]) -> str:
    header_parts: list[str] = []
    for row in rows[:6]:
        for cell in row[:8]:
            value = _normalize_spaces(cell)
            if value:
                header_parts.append(value)
    return _normalize_spaces(" ".join(header_parts))


def _detect_project_type(header_text: str) -> str:
    normalized = _normalize_key(header_text)

    if re.search(r"\bперв\w*\s+междисциплинар\w*\s+проект\w*", normalized):
        return PROJECT_TYPE_MP1
    if re.search(r"\bвтор\w*\s+междисциплинар\w*\s+проект\w*", normalized):
        return PROJECT_TYPE_MP2

    if "мп1" in normalized or "mp1" in normalized:
        return PROJECT_TYPE_MP1
    if "мп2" in normalized or "mp2" in normalized:
        return PROJECT_TYPE_MP2

    if re.search(r"\bперв\w*\b", normalized):
        return PROJECT_TYPE_MP1
    if re.search(r"\bвтор\w*\b", normalized):
        return PROJECT_TYPE_MP2

    return PROJECT_TYPE_MP2


def _find_row_index(rows: list[list[str]], labels: tuple[str, ...]) -> int | None:
    target_labels = {_normalize_label(label) for label in labels}

    for index, row in enumerate(rows):
        candidates = []
        if row:
            candidates.append(row[0])
            candidates.extend(row[1:3])
        for candidate in candidates:
            if _normalize_label(candidate) in target_labels:
                return index
    return None


def _find_all_row_indices(rows: list[list[str]], labels: tuple[str, ...]) -> list[int]:
    target_labels = {_normalize_label(label) for label in labels}
    result: list[int] = []
    for index, row in enumerate(rows):
        candidates = []
        if row:
            candidates.append(row[0])
            candidates.extend(row[1:3])
        if any(_normalize_label(candidate) in target_labels for candidate in candidates):
            result.append(index)
    return result


def _cell(rows: list[list[str]], row_index: int, col_index: int) -> str:
    if row_index < 0 or row_index >= len(rows):
        return ""
    row = rows[row_index]
    if col_index < 0 or col_index >= len(row):
        return ""
    return str(row[col_index] or "").strip()


def _extract_start_year(rows: list[list[str]], header_text: str) -> int:
    header_year = _extract_first_year(header_text)
    if header_year is not None:
        return header_year

    probe = " ".join(" ".join(row[:6]) for row in rows[:6])
    probe_year = _extract_first_year(_fix_mojibake(probe))
    if probe_year is not None:
        return probe_year
    return datetime.now().year


def _extract_first_year(text: str) -> int | None:
    years = [int(value) for value in re.findall(r"(20\d{2})", str(text or ""))]
    for year in years:
        if 2016 <= year <= 2100:
            return year
    return None


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


def _build_short_description(project_name: str, category: str, project_type: str) -> str:
    if len(category) >= 3:
        return category[:1000]
    return f"Проект {project_type}: {project_name}"[:1000]


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

            if label and not re.fullmatch(r"(?:№|#)?\s*\d+\.?", label):
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
