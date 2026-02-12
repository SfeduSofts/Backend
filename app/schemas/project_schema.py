from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class TeamName(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    type: str = Field(..., min_length=3, max_length=3)
    year: int = Field(..., ge=2016)
    description: str = Field(..., min_length=3, max_length=1000)
    mentor: str = Field(..., max_length=100)
    

class ProjectCreate(ProjectBase):
    slug: str = Field(..., min_length=3, max_length=255)
    protected: bool = Field(default=False)
    mentor_email: str = Field(..., max_length=255)
    photo_src: Optional[str] = Field(None, max_length=255)
    pdf_src: Optional[str] = Field(None, max_length=255)
    full_description: Optional[str] = Field(None, max_length=1000)

class ProjectResponseFull(ProjectBase):
    photo_src: Optional[str] = Field(None, max_length=255)
    teamNames: Optional[list[TeamName]] = Field(None)
    pdf_src: Optional[str] = Field(None, max_length=255)
    full_description: Optional[str] = Field(None, max_length=1000)
    
    model_config = ConfigDict(from_attributes=True)

class ProjectResponseShort(ProjectBase):
    model_config = ConfigDict(from_attributes=True)