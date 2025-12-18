from pydantic import BaseModel, Field
from typing import Optional

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    type: str = Field(..., min_length=3, max_length=3)
    year: int = Field(..., ge=2016)
    id: str = Field(..., max_length=36)
    description = Field(..., min_length=3, max_length=1000)
    mentor_name = Field(..., max_length=100)
    

class ProjectCreate(ProjectBase):
    slug: str = Field(..., min_length=3, max_length=255)
    protected: bool = Field(default=False)
    mentor_email: str = Field(..., max_length=255)
    photo_src: Optional[str] = Field(None, max_length=255)
    pdf_src: Optional[str] = Field(None, max_length=255)
    team_id: Optional[int] = Field(None, ge=1)
    full_description: Optional[str] = Field(None, max_length=1000)

class ProjectResponseFull(ProjectBase):
    photo_src: Optional[str] = Field(None, max_length=255)
    team_id: Optional[int] = Field(None, ge=1)
    pdf_src: Optional[str] = Field(None, max_length=255)
    full_description: Optional[str] = Field(None, max_length=1000)

class ProjectResponseShort(ProjectBase):
    pass