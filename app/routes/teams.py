from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.project_schema import TeamName, TeamNamesUpdate
from ..schemas.student_schema import TeamStudent, TeamStudentsUpdate
from ..services.team_service import TeamService

router = APIRouter(prefix="", tags=["teams"])


@router.get("/{project_id}/teams", response_model=List[TeamName], status_code=status.HTTP_200_OK)
def get_teams(project_id: int, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.get_teams(project_id)


@router.put("/{project_id}/teams", response_model=List[TeamName], status_code=status.HTTP_200_OK)
def update_teams(project_id: int, payload: TeamNamesUpdate, db: Session = Depends(get_db)):
    service = TeamService(db)
    return service.update_teams(project_id, payload.teamNames)


@router.get("/{team_name}/students", response_model=List[TeamStudent], status_code=status.HTTP_200_OK)
def get_students_by_team_name(
    team_name: str,
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    service = TeamService(db)
    return service.get_team_students(team_name, project_id=project_id)


@router.put("/{team_name}/students", response_model=List[TeamStudent], status_code=status.HTTP_200_OK)
def update_students_by_team_name(
    team_name: str,
    payload: TeamStudentsUpdate,
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    service = TeamService(db)
    return service.update_team_students(team_name, payload.students, project_id=project_id)
