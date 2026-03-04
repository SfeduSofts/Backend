from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from ..database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    protected = Column(Boolean, default=False)
    type = Column(String(3), nullable=False)
    year = Column(Integer, nullable=False)
    mentor = Column(String(100), nullable=False)
    full_description = Column(Text, nullable=True)

    teams = relationship("Team", back_populates="project")

    def __repr__(self):
        return f"<Project(name={self.name}, protected={self.protected}, years={self.year})>"