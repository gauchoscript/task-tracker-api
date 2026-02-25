from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.notifications import router as notifications_router
from app.middleware.cloudfront import CloudFrontForwardedProtoMiddleware

app = FastAPI(title=settings.PROJECT_NAME, redirect_slashes=False)

app.add_middleware(CloudFrontForwardedProtoMiddleware)

cors_kwargs = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if settings.ENVIRONMENT == "development":
    # In development, we allow any origin via regex to facilitate mobile/local testing
    cors_kwargs["allow_origin_regex"] = r"https?://.*"
else:
    # In production, we require explicit origins
    cors_kwargs["allow_origins"] = [str(origin) for origin in settings.backend_cors_origins]

app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(notifications_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Task Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
