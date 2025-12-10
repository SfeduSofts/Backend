from pydantic import BaseModel, Field
from typing import Optional

class StudentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    role: str = Field(..., min_length=3, max_length=50)
    photo_src: Optional[str] = Field(None, max_length=255)

class StudentResponse(StudentBase):
    pass

class StudentCreate(StudentBase):
    academic_year: int = Field(..., ge=1, le=6)
    email: str = Field(..., max_length=255)
    team_id: int = Field(..., ge=1)
    