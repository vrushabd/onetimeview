from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./onetime.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and automatically add any missing columns"""
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate schema: ensure columns added in updates exist in existing tables
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        if "secrets" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("secrets")}
            required_cols = {
                "webhook_url": "VARCHAR(500)",
                "cloud_url": "VARCHAR(500)",
                "cloud_public_id": "VARCHAR(255)",
                "cloud_resource_type": "VARCHAR(20)",
            }
            with engine.connect() as conn:
                for col, col_type in required_cols.items():
                    if col not in existing_cols:
                        conn.execute(text(f"ALTER TABLE secrets ADD COLUMN {col} {col_type}"))
                        print(f"✅ Auto-migrated DB: added column {col}")
                conn.commit()
    except Exception as e:
        print(f"⚠️ Warning during auto-migration: {e}")
