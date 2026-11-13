"""
Database Connection & Session Management
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

# Primary location: data/sqlite/shopmart.db; fallback: database/shopmart.db
primary_db = os.path.join(PROJECT_ROOT, "data", "sqlite", "shopmart.db")
db_path = primary_db
if not os.path.exists(db_path):
    fallback_db = os.path.join(BASE_DIR, "shopmart.db")
    if os.path.exists(fallback_db):
        db_path = fallback_db
    else:
        parent_db = os.path.join(os.path.dirname(BASE_DIR), "shopmart.db")
        if os.path.exists(parent_db):
            db_path = parent_db

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
