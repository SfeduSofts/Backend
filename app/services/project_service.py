from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.team_repository import TeamRepository
from app.services.mp2_sheet_import import (
    DEFAULT_MP2_SHEET_URL,
    PROJECT_TYPE_MP2,
    parse_projects_sheet,
)
from app.schemas.project_schema import (
    ProjectCreate,
    ProjectResponseFull,
    ProjectResponseShort,
    ProjectUpdate,
    TeamName,
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
                team_names = [str(team.get("name") or "").strip() for team in teams if str(team.get("name") or "").strip()]
                team_service.update_teams(created_project.id, team_names)

                for team in teams:
                    team_name = str(team.get("name") or "").strip()
                    if not team_name:
                        continue
                    students = team.get("students", [])
                    team_service.update_team_students(team_name, students, project_id=created_project.id)

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

        if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Only JPEG and PNG are allowed.",
            )

        if image.content_type == "image/jpeg":
            image_extension = "jpeg"
        elif image.content_type == "image/png":
            image_extension = "png"
        else:
            image_extension = "jpg"

        image_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.{image_extension}"

        with open(image_path, "wb") as file:
            file.write(image.file.read())

        return self._map_project_to_full_response(project)

    def upload_pdf(self, project_id: int, pdf: UploadFile) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        pdf_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.pdf"

        with open(pdf_path, "wb") as file:
            file.write(pdf.file.read())

        return self._map_project_to_full_response(project)

    def get_project_image(self, project_id: int) -> FileResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        image_path_jpeg = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.jpeg"
        image_path_png = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.png"
        image_path_jpg = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.jpg"

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

        pdf_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.pdf"

        if pdf_path.exists():
            response = FileResponse(pdf_path, media_type="application/pdf")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")

    def delete_project_image(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        image_path_jpeg = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.jpeg"
        image_path_png = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.png"
        image_path_jpg = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.jpg"

        if image_path_jpeg.exists():
            image_path_jpeg.unlink()
        if image_path_png.exists():
            image_path_png.unlink()
        if image_path_jpg.exists():
            image_path_jpg.unlink()

    def delete_project_pdf(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        pdf_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.pdf"
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
