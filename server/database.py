from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from server.models import Base

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dux_user:dux_password@localhost:5432/dux")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all tables
    """
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """
    Context manager for database sessions
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Dependency for FastAPI endpoints to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
