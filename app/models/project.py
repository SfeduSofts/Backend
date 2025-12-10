from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    protected = Column(Boolean, default=False)
    type = Column(String(3), nullable=False)
    protect_year = Column(String(4), nullable=False)
    photo_src = Column(String(255), nullable=True)
    mentor_name = Column(String(100), nullable=False)
    mentor_email = Column(String(255), nullable=False)

    team = relationship("Team", back_populates="projects")

    def __repr__(self):
        return f"<Project(name={self.name}, protected={self.protected}, years={self.protect_year})>"