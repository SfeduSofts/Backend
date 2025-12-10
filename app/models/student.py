from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(Integer, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    role = Column(String(50), nullable=False)
    photo_src = Column(String(255), nullable=True)

    team = relationship("Team", back_populates="students")

    def __repr__(self):
        return f"<Student(name={self.name}, email={self.email})>"