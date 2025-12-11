"""
Database configuration and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/muds_matching.db")

# Create engine with optimized SQLite settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
)


# Enable WAL mode for better SQLite performance
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance"""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session

    Yields:
        Session: Database session

    Examples:
        >>> from fastapi import Depends
        >>> @app.get("/users")
        >>> def get_users(db: Session = Depends(get_db)):
        >>>     return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables

    Note:
        This should be called before starting the application
        In production, use Alembic migrations instead
    """
    from app import models  # Import here to avoid circular imports

    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
