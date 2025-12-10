from sqlalchemy.orm import Session
from app.repositories.student_repository import StudentRepository
from app.schemas.student_schema import StudentResponse, StudentCreate
from fastapi import HTTPException, status

class StudentService:
    def __init__(self, db: Session):
        self.student_repository = StudentRepository(db)

    def get_all_students(self) -> list[StudentResponse]:
        students = self.student_repository.get_all()
        return [StudentResponse.model_validate(student) for student in students]
    
    def get_student_by_id(self, student_id: int) -> StudentResponse:
        student = self.student_repository.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        return StudentResponse.model_validate(student)
    
    def create_student(self, student_data: StudentCreate) -> StudentResponse:
        student = self.student_repository.create_student(student_data)
        return StudentResponse.model_validate(student)
    
    def get_student_by_email(self, email: str) -> StudentResponse:
        student = self.student_repository.get_by_email(email)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        return StudentResponse.model_validate(student)
    
    def get_students_by_team_id(self, team_id: int) -> list[StudentResponse]:
        # @TODO: добавить обработку отстутствия команды
        students = self.student_repository.get_by_team_id(team_id)
        return [StudentResponse.model_validate(student) for student in students]