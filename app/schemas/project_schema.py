from pydantic import BaseModel, Field
from typing import Optional

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    type: str = Field(..., min_length=3, max_length=3)
    protect_year: int = Field(..., ge=2016)
    photo_src: Optional[str] = Field(None, max_length=255)
    

class ProjectCreate(ProjectBase):
    slug: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10, max_length=1000)
    protected: bool = Field(default=False)
    mentor_name: str = Field(..., max_length=100)
    mentor_email: str = Field(..., max_length=255)

class ProjectResponseFull(ProjectCreate):
    id: str = Field(..., max_length=36)

class ProjectResponseShort(ProjectBase):
    pass