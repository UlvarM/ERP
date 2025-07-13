# database.py
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from models import Base

DATABASE_URL = "sqlite:///./warehouse.db"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def _run_migrations() -> None:
    cfg = Config(str(Path(__file__).with_name("alembic.ini")))
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(cfg, "head")

def init_db() -> None:
    _run_migrations()
