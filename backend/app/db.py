# backend/app/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Path to SQLite DB file
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nutrition.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Create the engine
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite + FastAPI
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure SQLite tables exist before use; no inputs, no return value.
def init_db():
    """Creates all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

# Yield a database session for request lifecycles.
# Input: none (FastAPI injects); Output: generator yielding a SQLAlchemy Session.
def get_db():
    """
    Dependency for FastAPI routes.
    Example:
        db = next(get_db())
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
