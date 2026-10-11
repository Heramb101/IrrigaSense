import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("irrigasense.db")

# Use SQLite for development, configurable via env var
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./irrigasense.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

    # Backward-compatible schema migration for existing tables
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        with engine.begin() as conn:
            if "users" in tables:
                user_cols = [c["name"] for c in inspector.get_columns("users")]
                if "username" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(50)"))
                if "password_hash" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"))

            if "assessments" in tables:
                asmt_cols = [c["name"] for c in inspector.get_columns("assessments")]
                if "user_id" not in asmt_cols:
                    conn.execute(text("ALTER TABLE assessments ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_assessments_user_id ON assessments (user_id)"))
    except Exception as e:
        logger.debug("Database migration note: %s", str(e))
