from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.team_service import TeamService
from ..schemas.project_schema import TeamName

router = APIRouter(
    prefix="",
    tags=["teams"]
)

@router.get("/{project_id}/teams", response_class=List[TeamName], status_code=status.HTTP_200_OK)
def get_teams(project_id: int, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_teams(project_id)