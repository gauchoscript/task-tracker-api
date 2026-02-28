from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from contextlib import asynccontextmanager

# Create async engine for the main API
engine = create_async_engine(settings.get_database_url(), echo=True)

# Create async session factory for the main API
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create async engine for workers (uses NullPool to avoid sharing/event loop issues)
worker_engine = create_async_engine(
    settings.get_database_url(), 
    echo=True,
    poolclass=NullPool
)

# Create async session factory for workers
WorkerSessionLocal = sessionmaker(
    bind=worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Context manager for use outside of FastAPI (e.g., Celery workers)
@asynccontextmanager
async def async_session_maker():
    """Async context manager for database sessions in workers using the worker engine."""
    async with WorkerSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
