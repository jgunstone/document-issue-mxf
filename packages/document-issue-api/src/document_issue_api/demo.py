"""Disposable, seeded API demo. Never initializes or migrates a configured database."""

import datetime
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from document_issue.enums import DocumentTypeEnum, RoleEnum, StatusRevisionEnum
from fastapi import FastAPI
from sqlalchemy import URL, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from document_issue_api.database import enable_sqlite_foreign_keys, get_db, session_scope
from document_issue_api.document.crud import post_document
from document_issue_api.document.schemas import DocumentBasePost
from document_issue_api.document_role.crud import post_document_role
from document_issue_api.issue.crud import post_issue
from document_issue_api.issue.schemas import IssueBasePost
from document_issue_api.main import create_app
from document_issue_api.models import Base
from document_issue_api.person.crud import post_person
from document_issue_api.person.schemas import PersonPost
from document_issue_api.project.crud import post_project
from document_issue_api.project.schemas import ProjectPost
from document_issue_api.project_role.crud import post_project_role
from document_issue_api.role.crud import post_role
from document_issue_api.role.schemas import RolePost


def seed_demo(db: Session) -> None:
    """Create validated, related examples using the API's normal write operations."""
    project = post_project(db, ProjectPost(
        project_number=10001,
        project_name="Demo Community Library",
        project_address="1 Example Street",
        client_name="Example Council",
    ))
    for initials, name, role_name in (
        ("AA", "Alex Example", RoleEnum.director_in_charge),
        ("SS", "Sam Sample", RoleEnum.project_engineer),
    ):
        person = post_person(db, PersonPost(initials=initials, full_name=name))
        role = post_role(db, RolePost(role_name=role_name))
        post_project_role(db, project.id, role.id, person.id)

    for sequence, title, document_type in (
        (1, "Demo equipment schedule", DocumentTypeEnum.es),
        (2, "Demo plantroom schedule", DocumentTypeEnum.prs),
    ):
        document = post_document(db, DocumentBasePost(
            project_id=project.id,
            document_code=f"10001-MXF-XX-XX-SH-M-{sequence:05d}",
            document_description=title,
            document_type=document_type,
            notes=["Fictional data for trying the API. Changes reset when the demo restarts."],
            format_configuration={"output_author": True, "output_checked_by": True},
        ))
        for assignment in project.project_role:
            post_document_role(db, assignment.role_id, document.id)
        for number, date, status in (
            (1, datetime.date(2025, 1, 15), StatusRevisionEnum.S2_P),
            (2, datetime.date(2025, 2, 1), StatusRevisionEnum.S3_P),
        ):
            post_issue(db, document.id, IssueBasePost(
                revision_number=number,
                date=date,
                status_revision=status,
                author="SS",
                checked_by="AA",
                issue_notes="Initial issue" if number == 1 else "Updated following review",
            ))


@asynccontextmanager
async def demo_lifespan(app: FastAPI):
    # One private file per server process: normal SQLite connections/transactions,
    # without the cross-request transaction sharing of an in-memory StaticPool.
    with TemporaryDirectory(prefix="document-issue-demo-") as directory:
        engine = create_engine(
            URL.create("sqlite", database=str(Path(directory) / "demo.db")),
            connect_args={"check_same_thread": False},
        )
        event.listen(engine, "connect", enable_sqlite_foreign_keys)
        sessions = sessionmaker(bind=engine, autoflush=False)

        def demo_db():
            with session_scope(sessions) as db:
                yield db

        try:
            Base.metadata.create_all(engine)
            with session_scope(sessions) as db:
                seed_demo(db)
            app.dependency_overrides[get_db] = demo_db
            logging.getLogger("uvicorn.error").info(
                "Disposable demo database seeded. Try /docs or /document_issue/1. "
                "Changes reset on restart/reload; configured databases are untouched.",
            )
            yield
        finally:
            app.dependency_overrides.pop(get_db, None)
            engine.dispose()


def create_demo_app() -> FastAPI:
    """Entry point for Uvicorn's --factory mode and unmodified-lifespan tests."""
    app = create_app(lifespan=demo_lifespan)
    app.description += (
        "\n\n**Demo mode:** fictional projects, people, roles, documents and issues "
        "are preloaded. All changes reset on restart or code reload. "
        "Start with `/document_issue/1`."
    )
    return app
