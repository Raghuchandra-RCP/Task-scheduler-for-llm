# Database package
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import time
from config import DATABASE_URL

# Try to create engine with minimal connection settings
try:
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        pool_timeout=30,
        connect_args={
            "connect_timeout": 10,
            "application_name": "insightsedge_app"
        }
    )
    print("Database engine created successfully")
except Exception as e:
    print(f"Failed to create database engine: {e}")
    # Fallback to no pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=None,  # Disable connection pooling
        connect_args={
            "connect_timeout": 5,
            "application_name": "insightsedge_app"
        }
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    # Skip connection testing to avoid timeout issues
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()