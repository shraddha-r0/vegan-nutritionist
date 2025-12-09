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
    connect_args={"check_same_thread": False}  # Allow reuse across threads (e.g., Streamlit)
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure SQLite tables exist before use; no inputs, no return value.
def init_db():
    """Creates all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

# Yield a database session for scripts or background jobs that still need ORM access.
def get_db():
    """
    Simple generator that mirrors the old FastAPI dependency, kept for utility scripts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
