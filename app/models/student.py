from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(Integer, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)

    team = relationship("Team", back_populates="students")

    def __repr__(self):
        return f"<Student(name={self.name}, email={self.email})>"