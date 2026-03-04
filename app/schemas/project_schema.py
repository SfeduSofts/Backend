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
    protected: bool = Field(default=False)
    full_description: Optional[str] = Field(None, max_length=1000)

class ProjectResponseFull(ProjectBase):
    id: int
    teamNames: Optional[list[TeamName]] = Field(None)
    full_description: Optional[str] = Field(None, max_length=1000)
    protected: Optional[bool] = Field(None)
    
    model_config = ConfigDict(from_attributes=True)

class ProjectResponseShort(ProjectBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    type: Optional[str] = Field(None, min_length=3, max_length=3)
    year: Optional[int] = Field(None, ge=2016)
    description: Optional[str] = Field(None, min_length=3, max_length=1000)
    mentor: Optional[str] = Field(None, max_length=100)
    full_description: Optional[str] = Field(None, max_length=1000)
    protected: Optional[bool] = Field(None)
    
