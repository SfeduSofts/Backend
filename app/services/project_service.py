from sqlalchemy.orm import Session
from app.schemas.project_schema import ProjectResponseFull, ProjectResponseShort, ProjectCreate, ProjectUpdate
from app.repositories.project_repository import ProjectRepository
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path

class ProjectService:
    # ------------------------------ПРОЕКТЫ----------------------------------------------------------
    def __init__(self, db: Session):
        self.project_repository = ProjectRepository(db)

    def get_all_projects(self) -> list[ProjectResponseShort]:
        projects = self.project_repository.get_all()
        return [ProjectResponseShort.model_validate(project) for project in projects]
    
    def get_project_by_id(self, project_id: int) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return ProjectResponseFull.model_validate(project)
    
    def create_project(self, project_data: ProjectCreate) -> ProjectResponseFull:
        project = self.project_repository.create_project(project_data)
        return ProjectResponseFull.model_validate(project)
    
    def update_project(self, project_id: int, project_data: ProjectUpdate) -> ProjectResponseFull:
        project = self.project_repository.update_project(project_id, project_data)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return ProjectResponseFull.model_validate(project)
    
    def delete_project(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        self.delete_project_image(project_id)
        self.delete_project_pdf(project_id)
        self.project_repository.delete_project(project_id)

    # -------------------------------------------ФАЙЛЫ----------------------------------------------------------
    def upload_image(self, project_id: int, image: UploadFile) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Only JPEG and PNG are allowed.")

        if image.content_type == "image/jpeg":
            image_extension = "jpeg"
        elif image.content_type == "image/png":
            image_extension = "png"
        elif image.content_type == "image/jpg":
            image_extension = "jpg"

        image_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.{image_extension}"

        with open(image_path, "wb") as f:
            f.write(image.file.read())

        return ProjectResponseFull.model_validate(project)
    
    def upload_pdf(self, project_id: int, pdf: UploadFile) -> ProjectResponseFull:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        pdf_path = Path(__file__).resolve().parent.parent / "static" / f"{project_id}.pdf"

        with open(pdf_path, "wb") as f:
            f.write(pdf.file.read())

        return ProjectResponseFull.model_validate(project)
    
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
        elif image_path_png.exists():
            response = FileResponse(image_path_png, media_type="image/png")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        elif image_path_jpg.exists():
            response = FileResponse(image_path_jpg, media_type="image/jpeg")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response
        else:
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
        else:
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