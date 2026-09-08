"""
SQLAlchemy engine / session management.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.app.config import get_settings

settings = get_settings()

# pool_pre_ping avoids "server closed the connection unexpectedly" after idle periods,
# which matters a lot for a long-running scheduler process.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Context manager for use OUTSIDE of FastAPI (scheduler, scripts)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    from backend.app import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)
