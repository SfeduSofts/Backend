from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.admin_schema import Admin as AdminSchema
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(tags=["auth"])


@router.get("/login")
def login():
    return AuthService.microsoft_login()

@router.get("/microsoft/callback")
async def microsoft_callback(code: str, db: Session = Depends(get_db), request: Request = None):
    return await AuthService.microsoft_callback(code=code, db=db, request=request)

@router.post("/admins", response_model=AdminSchema, status_code=201)
def create_admin(admin: AdminSchema, db: Session = Depends(get_db), current_user=Depends(AuthService.get_current_user)):
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    if not current_user or current_user.get("email") != superadmin_email:
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuthService(db)
    return service.add_admin(admin.email)

@router.get("/admins/{email}", response_model=AdminSchema)
def get_admin(email: str, db: Session = Depends(get_db), current_user=Depends(AuthService.get_current_user)):
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    if not current_user or current_user.get("email") != superadmin_email:
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuthService(db)
    admin = service.get_admin_by_email(email)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@router.get("/admins", response_model=list[AdminSchema])
def get_all_admins(db: Session = Depends(get_db), current_user=Depends(AuthService.get_current_user)):
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    if not current_user or current_user.get("email") != superadmin_email:
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuthService(db)
    return service.admin_repository.db.query(Admin).all()

@router.delete("/admins/{email}", status_code=204)
def delete_admin(email: str, db: Session = Depends(get_db), current_user=Depends(AuthService.get_current_user)):
    superadmin_email = os.getenv("SUPERADMIN_EMAIL")
    if not current_user or current_user.get("email") != superadmin_email:
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuthService(db)
    admin = service.get_admin_by_email(email)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    service.admin_repository.delete(admin)
    