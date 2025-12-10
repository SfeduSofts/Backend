from fastapi import FastAPI
from app.routes import project_router, student_router
from app.database import init_db
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=settings.app_name, 
    debug=settings.debug, 
    docs_url="/docs" if settings.debug else None, 
    redoc_url="/redoc" if settings.debug else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(project_router, prefix="/projects")
app.include_router(student_router, prefix="/students")
