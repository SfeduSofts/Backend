from fastapi import FastAPI
from app.routes import project_router, student_router, team_router, auth_router
from app.database import init_db
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.services.auth_service import AuthService

app = FastAPI(
    title=settings.app_name, 
    debug=settings.debug, 
    docs_url="/docs" if settings.debug else None, 
    redoc_url="/redoc" if settings.debug else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router, prefix="/api/projects")
app.include_router(student_router, prefix="/api/students")
app.include_router(team_router, prefix="/api/teams")
app.include_router(auth_router, prefix="/auth")

init_db()
