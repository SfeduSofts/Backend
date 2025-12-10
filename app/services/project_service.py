from sqlalchemy.orm import Session
from app.schemas.project_schema import ProjectResponseFull, ProjectResponseShort, ProjectCreate
from app.repositories.project_repository import ProjectRepository
from fastapi import HTTPException, status

class ProjectService:
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
    
    def get_project_by_slug(self, slug: str) -> ProjectResponseFull:
        project = self.project_repository.get_by_slug(slug)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return ProjectResponseFull.model_validate(project)