"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..config import settings
from .models import Base


# Create engine with connection pooling
def get_engine():
    """Get SQLAlchemy engine."""
    if settings.database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            settings.database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=settings.debug
        )
    else:
        # PostgreSQL and other databases
        engine = create_engine(
            settings.database_url,
            echo=settings.debug
        )
    return engine


# Create sessionmaker
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Get database session."""
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
