from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class StudentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    role: str = Field(..., min_length=3, max_length=50)
    photo_src: Optional[str] = Field(None, max_length=255)

class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

class StudentCreate(StudentBase):
    academic_year: int = Field(..., ge=1, le=6)
    email: str = Field(..., max_length=255)
    team_id: int = Field(..., ge=1)


class TeamStudent(BaseModel):
    name: str = Field("", max_length=100)
    role: str = Field("", max_length=50)


class TeamStudentsUpdate(BaseModel):
    students: list[TeamStudent] = Field(default_factory=list)
    
