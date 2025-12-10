from sqlalchemy.orm import Session
from app.models.student import Student
from typing import List, Optional
from app.schemas.student_schema import StudentCreate

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
    
    def get_by_team_id(self, team_id: str) -> List[Student]:
        return self.db.query(Student).filter(Student.team_id == team_id).all()