"""Run all API tests against fresh temporary databases, never api-dev.env data."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from document_issue_api import database
from document_issue_api.models import Base
from setup_test_client import client as test_client


@pytest.fixture(autouse=True)
def db_engine(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", database.enable_sqlite_foreign_keys)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(database, "create_session", sessionmaker(bind=engine, autoflush=False))
    yield engine
    engine.dispose()


@pytest.fixture
def client(db_engine):
    with test_client:
        yield test_client


@pytest.fixture
def db(db_engine):
    with Session(db_engine) as session:
        yield session
