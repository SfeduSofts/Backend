from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.project_repository import ProjectRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.team_repository import TeamRepository
from app.models.team import Team
from app.schemas.project_schema import TeamName
from app.schemas.student_schema import TeamStudent


class TeamService:
    def __init__(self, db: Session):
        self.project_repository = ProjectRepository(db)
        self.team_repository = TeamRepository(db)
        self.student_repository = StudentRepository(db)

    def get_teams(self, project_id: int) -> List[TeamName]:
        self._ensure_project_exists(project_id)
        teams = self.team_repository.get_by_project_id(project_id)
        return [TeamName(name=team.name) for team in teams]

    def update_teams(self, project_id: int, team_names: List[str]) -> List[TeamName]:
        self._ensure_project_exists(project_id)

        normalized_names = self._normalize_team_names(team_names)
        existing_teams = self.team_repository.get_by_project_id(project_id)
        existing_by_name = {team.name: team for team in existing_teams}

        to_keep = set(normalized_names)

        for team in existing_teams:
            if team.name in to_keep:
                continue
            self.student_repository.delete_by_team_id(team.id)
            self.team_repository.delete_team(team)

        for team_name in normalized_names:
            if team_name in existing_by_name:
                continue
            self.team_repository.create_team(team_name, project_id)

        return [TeamName(name=name) for name in normalized_names]

    def get_team_students(self, team_name: str, project_id: Optional[int] = None) -> List[TeamStudent]:
        normalized_team_name = self._normalize_team_name(team_name)
        if not normalized_team_name:
            return []

        team = self._resolve_team(normalized_team_name, project_id)
        if not team:
            return []

        students = self.student_repository.get_by_team_id(team.id)
        return [TeamStudent(name=student.name, role=student.role) for student in students]

    def update_team_students(
        self,
        team_name: str,
        students: List[TeamStudent | dict],
        project_id: Optional[int] = None,
    ) -> List[TeamStudent]:
        normalized_team_name = self._normalize_team_name(team_name)
        if not normalized_team_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Team name cannot be empty",
            )

        team = self._resolve_team(normalized_team_name, project_id)
        if not team:
            if project_id is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found. Pass project_id to create a new team.",
                )
            self._ensure_project_exists(project_id)
            team = self.team_repository.create_team(normalized_team_name, project_id)

        normalized_students: List[TeamStudent] = []
        for student in students:
            name, role = self._extract_student_name_and_role(student)
            if not name:
                continue
            normalized_students.append(TeamStudent(name=name, role=role))

        saved_students = self.student_repository.replace_by_team_id(team.id, normalized_students)
        return [TeamStudent(name=student.name, role=student.role) for student in saved_students]

    def _ensure_project_exists(self, project_id: int) -> None:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    def _resolve_team(self, team_name: str, project_id: Optional[int]) -> Optional[Team]:
        if project_id is not None:
            return self.team_repository.get_by_name_and_project(team_name, project_id)

        by_name = self.team_repository.get_by_name(team_name)
        if not by_name:
            return None
        if len(by_name) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Multiple teams share this name. Pass project_id.",
            )
        return by_name[0]

    def _normalize_team_names(self, team_names: List[str]) -> List[str]:
        result: List[str] = []
        seen = set()

        for name in team_names:
            normalized = self._normalize_team_name(name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)

        return result

    def _normalize_team_name(self, team_name: str) -> str:
        return str(team_name or "").strip()

    def _extract_student_name_and_role(self, student: TeamStudent | dict) -> tuple[str, str]:
        if isinstance(student, dict):
            name = str(student.get("name") or "").strip()
            role = str(student.get("role") or "").strip()
            return name, role

        return str(student.name or "").strip(), str(student.role or "").strip()

