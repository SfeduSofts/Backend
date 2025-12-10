from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.student_service import StudentService
from ..schemas.student_schema import StudentCreate, StudentResponse

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"]
)

@router.get("", response_model=List[StudentResponse], status_code=status.HTTP_200_OK)
def get_all_students(db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.get_all_students()

@router.get("/{student_id}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def get_student_by_id(student_id: int, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.get_student_by_id(student_id)

@router.get("/email/{student_email}", response_model=StudentResponse, status_code=status.HTTP_200_OK)
def get_student_by_email(student_email: str, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.get_student_by_email(student_email)

@router.get("/team/{team_id}", response_model=List[StudentResponse], status_code=status.HTTP_200_OK)
def get_students_by_team_id(team_id: int, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.get_students_by_team_id(team_id)

@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student_data: StudentCreate, db: Session = Depends(get_db)):
    service = StudentService(db)
    return service.create_student(student_data)