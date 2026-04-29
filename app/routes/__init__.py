from app.routes.projects import router as project_router
from app.routes.students import router as student_router
from app.routes.teams import router as team_router
from app.routes.auth import router as auth_router

__all__ = ["project_router", "student_router", "team_router", "auth_router"]
