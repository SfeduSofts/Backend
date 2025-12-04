from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    protected = Column(Boolean, default=False)
    number = Column(Integer, nullable=False)
    years = Column(String(9), nullable=False)

    team = relationship("Team", back_populates="projects")

    def __repr__(self):
        return f"<Project(name={self.name}, protected={self.protected}, years={self.years})>"