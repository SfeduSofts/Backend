import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.team_repository import TeamRepository
from app.schemas.project_schema import (
    ProjectCreate,
    ProjectResponseFull,
    ProjectResponseShort,
    ProjectUpdate,
    TeamName,
)
from app.services.mp2_sheet_import import (
    DEFAULT_MP2_SHEET_URL,
    PROJECT_TYPE_MP2,
    parse_projects_sheet,
)


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repository = ProjectRepository(db)
        self.team_repository = TeamRepository(db)
        self.student_repository = StudentRepository(db)

    # ------------------------------ Projects ------------------------------
    def get_all_projects(self) -> list[ProjectResponseShort]:
        projects = self.project_repository.get_all()
        return [ProjectResponseShort.model_validate(project) for project in projects]

    def get_project_by_id(self, project_id: int) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return self._map_project_to_full_response(project)

    def create_project(self, project_data: ProjectCreate) -> ProjectResponseFull:
        project = self.project_repository.create_project(project_data)
        return self._map_project_to_full_response(project)

    def update_project(self, project_id: int, project_data: ProjectUpdate) -> ProjectResponseFull:
        project = self.project_repository.update_project(project_id, project_data)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return self._map_project_to_full_response(project)

    def delete_project(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        teams = self.team_repository.get_by_project_id(project_id)
        for team in teams:
            self.student_repository.delete_by_team_id(team.id)
            self.team_repository.delete_team(team)

        self.delete_project_image(project_id)
        self.delete_project_pdf(project_id)
        self.project_repository.delete_project(project_id)

    def import_mp2_projects_from_sheet(self) -> dict:
        result = self.import_projects_from_sheet(DEFAULT_MP2_SHEET_URL)
        result["source"] = "google_sheet_mp2"
        return result

    def import_projects_from_sheet(self, sheet_url: str) -> dict:
        from app.services.team_service import TeamService

        try:
            parsed = parse_projects_sheet(sheet_url)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sheet URL: {error}",
            ) from error
        except Exception as error:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to load sheet: {error}",
            ) from error

        parsed_projects = parsed.get("projects", [])
        default_type = self._normalize_project_type(parsed.get("type"))
        default_year = self._normalize_project_year(parsed.get("year"))

        existing_projects = self.project_repository.get_all()
        existing_by_name = {self._normalize_key(project.name): project for project in existing_projects}

        created = 0
        skipped = 0
        errors: list[dict[str, str]] = []

        team_service = TeamService(self.db)

        for item in parsed_projects:
            project_name = str(item.get("name") or "").strip()
            if not project_name:
                continue

            key = self._normalize_key(project_name)
            if key in existing_by_name:
                skipped += 1
                continue

            try:
                created_project = self.project_repository.create_project(
                    ProjectCreate(
                        name=project_name[:255],
                        type=self._normalize_project_type(item.get("type"), default_type),
                        year=self._normalize_project_year(item.get("year"), default_year),
                        description=str(item.get("description") or f"Проект {default_type}: {project_name}")[:1000],
                        mentor=str(item.get("mentor") or "")[:100],
                        full_description=str(item.get("full_description") or project_name)[:1000],
                        protected=False,
                    )
                )

                teams = item.get("teams", [])
                team_names = [
                    str(team.get("name") or "").strip()
                    for team in teams
                    if str(team.get("name") or "").strip()
                ]
                team_service.update_teams(created_project.id, team_names)

                for team in teams:
                    team_name = str(team.get("name") or "").strip()
                    if not team_name:
                        continue
                    students = team.get("students", [])
                    team_service.update_team_students(team_name, students, project_id=created_project.id)

                for asset_error in self._import_project_documents_from_links(created_project.id, item):
                    errors.append({"project": project_name, "error": asset_error})

                existing_by_name[key] = created_project
                created += 1
            except Exception as error:  # noqa: BLE001
                errors.append({"project": project_name, "error": str(error)})

        return {
            "source": "google_sheet",
            "sheet_url": parsed.get("source_url") or sheet_url,
            "detected_type": default_type,
            "detected_year": default_year,
            "parsed": len(parsed_projects),
            "created": created,
            "skipped_existing": skipped,
            "errors": errors,
        }

    # ------------------------------- Files -------------------------------
    def upload_image(self, project_id: int, image: UploadFile) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        payload = image.file.read()
        image_extension = self._detect_image_extension(payload, image.content_type)
        if not image_extension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Only JPEG and PNG are allowed.",
            )

        self._save_image_bytes(project_id, payload, image.content_type, image_extension)
        return self._map_project_to_full_response(project)

    def upload_pdf(self, project_id: int, pdf: UploadFile) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        payload = pdf.file.read()
        if not self._looks_like_pdf(payload, pdf.content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF format.",
            )

        self._save_pdf_bytes(project_id, payload)
        return self._map_project_to_full_response(project)

    def get_project_image(self, project_id: int) -> FileResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        image_path_jpeg = self._get_static_dir() / f"{project_id}.jpeg"
        image_path_png = self._get_static_dir() / f"{project_id}.png"
        image_path_jpg = self._get_static_dir() / f"{project_id}.jpg"

        if image_path_jpeg.exists():
            response = FileResponse(image_path_jpeg, media_type="image/jpeg")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        if image_path_png.exists():
            response = FileResponse(image_path_png, media_type="image/png")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        if image_path_jpg.exists():
            response = FileResponse(image_path_jpg, media_type="image/jpeg")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    def get_project_pdf(self, project_id: int) -> FileResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        pdf_path = self._get_static_dir() / f"{project_id}.pdf"

        if pdf_path.exists():
            response = FileResponse(pdf_path, media_type="application/pdf")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")

    def delete_project_image(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        self._delete_project_image_files(project_id)

    def delete_project_pdf(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        pdf_path = self._get_static_dir() / f"{project_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()

    def _map_project_to_full_response(self, project) -> ProjectResponseFull:
        teams = self.team_repository.get_by_project_id(project.id)
        team_names = [TeamName(name=team.name) for team in teams]

        return ProjectResponseFull(
            id=project.id,
            name=project.name,
            description=project.description,
            protected=project.protected,
            type=project.type,
            year=project.year,
            mentor=project.mentor,
            full_description=project.full_description,
            teamNames=team_names,
        )

    def _normalize_key(self, value: str) -> str:
        return " ".join(str(value or "").strip().lower().split())

    def _normalize_project_type(self, value, default: str = PROJECT_TYPE_MP2) -> str:
        raw = str(value or "").strip().upper()
        if raw in {"МП1", "MP1"} or raw.endswith("1"):
            return "МП1"
        if raw in {"МП2", "MP2"} or raw.endswith("2"):
            return "МП2"
        return default

    def _normalize_project_year(self, value, default: int = 2025) -> int:
        try:
            year = int(value)
        except (TypeError, ValueError):
            return default
        if year < 2016:
            return default
        return year

    def _import_project_documents_from_links(self, project_id: int, item: dict) -> list[str]:
        errors: list[str] = []

        pdf_url = str(item.get("pdf_url") or "").strip()
        if pdf_url:
            try:
                payload, content_type = self._download_remote_file(pdf_url)
                if not self._looks_like_pdf(payload, content_type):
                    raise ValueError("linked PDF is not a valid PDF file")
                self._save_pdf_bytes(project_id, payload)
            except Exception as error:  # noqa: BLE001
                errors.append(f"Failed to import PDF: {error}")

        image_url = str(item.get("image_url") or "").strip()
        if image_url:
            try:
                payload, content_type = self._download_remote_file(image_url)
                self._save_image_bytes(project_id, payload, content_type)
            except Exception as error:  # noqa: BLE001
                errors.append(f"Failed to import image: {error}")

        return errors

    def _download_remote_file(self, source_url: str) -> tuple[bytes, str]:
        normalized_url = self._normalize_remote_file_url(source_url)
        request = Request(normalized_url, headers={"User-Agent": "Mozilla/5.0"})

        with urlopen(request, timeout=60) as response:
            payload = response.read()
            content_type = response.headers.get_content_type()

        return payload, str(content_type or "").lower()

    def _normalize_remote_file_url(self, source_url: str) -> str:
        raw_url = str(source_url or "").strip()
        if not raw_url:
            return ""

        parts = urlsplit(raw_url)
        if "drive.google.com" not in parts.netloc.lower():
            return raw_url

        query = parse_qs(parts.query)
        file_id = ""
        if query.get("id"):
            file_id = str(query["id"][0]).strip()

        if not file_id:
            match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", parts.path)
            if match:
                file_id = match.group(1)

        if file_id:
            return f"https://drive.google.com/uc?export=download&id={file_id}"

        return raw_url

    def _save_image_bytes(
        self,
        project_id: int,
        payload: bytes,
        content_type: str | None = None,
        image_extension: str | None = None,
    ) -> None:
        detected_extension = image_extension or self._detect_image_extension(payload, content_type)
        if not detected_extension:
            raise ValueError("linked image is not a supported JPEG or PNG file")

        image_path = self._get_static_dir() / f"{project_id}.{detected_extension}"
        self._delete_project_image_files(project_id)
        image_path.write_bytes(payload)

    def _save_pdf_bytes(self, project_id: int, payload: bytes) -> None:
        if not self._looks_like_pdf(payload):
            raise ValueError("linked PDF is not a valid PDF file")

        pdf_path = self._get_static_dir() / f"{project_id}.pdf"
        pdf_path.write_bytes(payload)

    def _detect_image_extension(self, payload: bytes, content_type: str | None = None) -> str:
        if payload.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if payload.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"

        normalized_content_type = str(content_type or "").lower()
        if normalized_content_type == "image/jpeg":
            return "jpeg"
        if normalized_content_type == "image/jpg":
            return "jpg"
        if normalized_content_type == "image/png":
            return "png"
        return ""

    def _looks_like_pdf(self, payload: bytes, content_type: str | None = None) -> bool:
        if payload.startswith(b"%PDF-"):
            return True
        return str(content_type or "").lower() == "application/pdf"

    def _delete_project_image_files(self, project_id: int) -> None:
        static_dir = self._get_static_dir()
        for extension in ("jpeg", "png", "jpg"):
            image_path = static_dir / f"{project_id}.{extension}"
            if image_path.exists():
                image_path.unlink()

    def _get_static_dir(self) -> Path:
        static_dir = Path(__file__).resolve().parent.parent / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        return static_dir
