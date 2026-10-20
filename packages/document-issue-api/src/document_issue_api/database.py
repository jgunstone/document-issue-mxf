from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from document_issue_api.env import ApiEnv


def enable_sqlite_foreign_keys(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")


@lru_cache(maxsize=1)
def get_engine():
    """Initialize the configured database only for normal API/database operations."""
    url = ApiEnv().DOCUMENTISSUE_DATABASE_URL
    engine = create_engine(
        url, connect_args={"check_same_thread": False} if url.startswith("sqlite:") else {},
    )
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", enable_sqlite_foreign_keys)
    return engine


def create_session() -> Session:
    return Session(bind=get_engine(), autoflush=False)


@contextmanager
def session_scope(session_factory):
    """Give normal and demo requests the same commit/rollback boundaries."""
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db():
    # Routes use Depends(..., scope="function") so commit errors reach the client
    # before response headers are sent, including on recent FastAPI versions.
    with session_scope(create_session) as db:
        yield db
