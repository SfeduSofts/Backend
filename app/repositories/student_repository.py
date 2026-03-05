import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student_schema import StudentCreate, TeamStudent


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_student(self, student_create: StudentCreate) -> Student:
        db_student = Student(**student_create.model_dump())
        self.db.add(db_student)
        self.db.commit()
        self.db.refresh(db_student)
        return db_student

    def get_by_id(self, student_id: int) -> Optional[Student]:
        return self.db.query(Student).filter(Student.id == student_id).first()

    def get_by_email(self, email: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.email == email).first()

    def get_by_name(self, name: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.name == name).first()

    def get_all(self) -> List[Student]:
        return self.db.query(Student).all()

    def get_by_team_id(self, team_id: int | str) -> List[Student]:
        return (
            self.db.query(Student)
            .filter(Student.team_id == str(team_id))
            .order_by(Student.id.asc())
            .all()
        )

    def delete_by_team_id(self, team_id: int | str) -> None:
        (
            self.db.query(Student)
            .filter(Student.team_id == str(team_id))
            .delete(synchronize_session=False)
        )
        self.db.commit()

    def replace_by_team_id(self, team_id: int | str, students: List[TeamStudent]) -> List[Student]:
        normalized_team_id = str(team_id)

        (
            self.db.query(Student)
            .filter(Student.team_id == normalized_team_id)
            .delete(synchronize_session=False)
        )

        saved_students: List[Student] = []
        for index, student in enumerate(students):
            name = (student.name or "").strip()
            role = (student.role or "").strip()

            if not name:
                continue

            db_student = Student(
                name=name,
                role=role,
                academic_year=1,
                email=self._build_system_email(normalized_team_id, index, name),
                team_id=normalized_team_id,
                photo_src=None,
            )
            self.db.add(db_student)
            saved_students.append(db_student)

        self.db.commit()

        for student in saved_students:
            self.db.refresh(student)

        return saved_students

    def _build_system_email(self, team_id: str, index: int, name: str) -> str:
        latin = re.sub(r"[^a-z0-9]+", "", name.lower())
        if not latin:
            latin = "student"
        return f"team{team_id}_student{index + 1}_{latin}@local.invalid"
