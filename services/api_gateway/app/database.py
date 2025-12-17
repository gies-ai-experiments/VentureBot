from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import get_settings

LOGGER = logging.getLogger(__name__)

settings = get_settings()

DEFAULT_SQLITE_PATH = "./data/chat.sqlite3"

database_url = settings.database_url or f"sqlite:///{DEFAULT_SQLITE_PATH}"

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def init_db() -> None:
    """Ensure the SQLite directory exists and create tables."""
    LOGGER.info("Initializing database: %s", database_url)
    if database_url.startswith("sqlite"):
        sqlite_path = database_url.replace("sqlite:///", "")
        directory = os.path.dirname(sqlite_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            LOGGER.debug("Created directory: %s", directory)
    from . import models  # noqa: WPS433 (late import to avoid circular)

    Base.metadata.create_all(bind=engine)
    LOGGER.info("Database tables created successfully")


def get_session() -> Generator[Session, None, None]:
    """Provide a SQLAlchemy session dependency for FastAPI routes."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Transactional scope helper for scripts or background jobs."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

