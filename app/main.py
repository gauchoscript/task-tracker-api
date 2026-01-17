from fastapi import FastAPI
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(auth_router)
app.include_router(tasks_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Task Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
