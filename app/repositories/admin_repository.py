from app.models.admin import Admin
from app.schemas.admin_schema import Admin as AdminSchema
from sqlalchemy.orm import Session
from typing import Optional

class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[Admin]:
        return self.db.query(Admin).filter(Admin.email == email).first()

    def create(self, admin: AdminSchema) -> AdminSchema:
        new_admin = Admin(email=admin.email)
        self.db.add(new_admin)
        self.db.commit()
        self.db.refresh(new_admin)
        return new_admin
    
    def delete(self, email: str) -> None:
        admin = self.get_by_email(email)
        if admin:
            self.db.delete(admin)
            self.db.commit()