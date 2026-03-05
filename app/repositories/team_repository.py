from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.team import Team


class TeamRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, team_id: int) -> Optional[Team]:
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_by_project_id(self, project_id: int) -> List[Team]:
        return (
            self.db.query(Team)
            .filter(Team.project_id == str(project_id))
            .order_by(Team.id.asc())
            .all()
        )

    def get_by_name_and_project(self, name: str, project_id: int) -> Optional[Team]:
        return (
            self.db.query(Team)
            .filter(Team.name == name, Team.project_id == str(project_id))
            .first()
        )

    def get_by_name(self, name: str) -> List[Team]:
        return self.db.query(Team).filter(Team.name == name).order_by(Team.id.asc()).all()

    def create_team(self, name: str, project_id: int) -> Team:
        team = Team(name=name, project_id=str(project_id))
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete_team(self, team: Team) -> None:
        self.db.delete(team)
        self.db.commit()
