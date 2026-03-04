from sqlalchemy.orm import Session
from app.schemas.project_schema import TeamName
from app.repositories.project_repository import ProjectRepository
from app.repositories.team_repository import TeamRepository
from fastapi import HTTPException, status

