from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)

    projects = relationship("Project", back_populates="team")

    def __repr__(self):
        return f"<Team(name={self.name}>"