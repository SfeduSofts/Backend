from sqlalchemy.orm import Session
from app.models.project import Project
from typing import List, Optional
from app.schemas.project_schema import ProjectCreate

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
    
    def get_by_slug(self, slug: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.slug == slug).first()

    def get_all(self) -> List[Project]:
        return self.db.query(Project).all()