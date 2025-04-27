from fastapi import APIRouter
from app.routes import habits, completions

api_router = APIRouter(prefix="/api")

api_router.include_router(habits.router, prefix="/habits", tags=["Habits"])
api_router.include_router(completions.router, prefix="/completions", tags=["Completions"])