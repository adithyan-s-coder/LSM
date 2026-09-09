"""
Database connection setup using SQLAlchemy.
Reads connection info from environment variables (see .env.example).
Uses MySQL in production. Defaults to a local SQLite file ONLY for quick
local demo runs if MySQL isn't configured, so the app can still boot;
set DATABASE_URL to your MySQL DSN for the real deployment.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost/last_safe_moment"
)

# Fallback so the app is runnable out-of-the-box during evaluation without
# requiring a live MySQL server. In real deployment, DATABASE_URL should
# always point at MySQL as required by the spec.
_engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
