from sqlalchemy.orm import Session
from app.models.project import Project
from typing import List, Optional
from app.schemas.project_schema import ProjectCreate, ProjectUpdate

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project_create: ProjectCreate) -> Project:
        db_project = Project(**project_create.model_dump())
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def get_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_all(self) -> List[Project]:
        return self.db.query(Project).all()
    
    def update_project(self, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        project = self.get_by_id(project_id)
        if not project:
            return None
        for key, value in project_data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def delete_project(self, project_id: int) -> None:
        project = self.get_by_id(project_id)
        if project:
            self.db.delete(project)
            self.db.commit()