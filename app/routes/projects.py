from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from ..database import get_db
from ..services.project_service import ProjectService
from ..schemas.project_schema import ProjectCreate, ProjectResponseFull, ProjectResponseShort, ProjectUpdate

router = APIRouter(
    prefix="",
    tags=["projects"]
)

@router.get("", response_model=List[ProjectResponseShort], status_code=status.HTTP_200_OK)
def get_all_projects(db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_all_projects()

@router.get("/{project_id}", response_model=ProjectResponseFull, status_code=status.HTTP_200_OK)
def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_project_by_id(project_id)

@router.get("/slug/{project_slug}", response_model=ProjectResponseFull, status_code=status.HTTP_200_OK)
def get_project_by_slug(project_slug: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_project_by_slug(project_slug)

@router.post("", response_model=ProjectResponseFull, status_code=status.HTTP_201_CREATED)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.create_project(project_data)

@router.put("/{project_id}", response_model=ProjectResponseFull, status_code=status.HTTP_200_OK)
def update_project(project_id: int, project_data: ProjectUpdate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.update_project(project_id, project_data)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.project_repository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    service.delete_project(project_id)
    return None