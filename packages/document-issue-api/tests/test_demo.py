"""Exercise the real demo lifespan and launcher, not the normal fresh-DB fixture."""

import hashlib
import os
import shlex
import signal
import socket
import sqlite3
import subprocess
import sys
import textwrap
import time
import tomllib
from pathlib import Path

import httpx
import pytest
from document_issue import DocumentIssue
from fastapi.testclient import TestClient

from document_issue_api.database import get_db
from document_issue_api.demo import create_demo_app
from document_issue_api.main import app as normal_app


@pytest.fixture(autouse=True)
def db_engine():
    """Override conftest's fixture: no schema creation or session-factory patch."""


@pytest.fixture
def demo_client():
    with TestClient(create_demo_app()) as client:
        yield client


def test_seeded_resources_are_readable(demo_client):
    for path in (
        "/", "/docs", "/openapi.json", "/schemas/", "/schemas/DocumentIssue",
        "/project/", "/project/1", "/person/", "/person/1", "/person/2",
        "/roles", "/role/1", "/role/2", "/project_roles/1/",
        "/documents/", "/document/1", "/document/2",
        "/document_roles/1/", "/document_roles/2/",
        "/issue/1", "/issue/2", "/issue/3", "/issue/4",
    ):
        response = demo_client.get(path)
        assert response.status_code == 200, (path, response.text)
    for document_id in (1, 2):
        response = demo_client.get(f"/document_issue/{document_id}")
        assert response.status_code == 200, response.text
        aggregate = DocumentIssue.model_validate(response.json())
        assert aggregate.project_name == "Demo Community Library"
        assert aggregate.director_in_charge == "AA"
        assert {role.initials for role in aggregate.document_role} == {"AA", "SS"}
        assert [issue.revision for issue in aggregate.issue_history] == ["P01", "P02"]
        assert aggregate.format_configuration.output_author is True


def test_demo_writes_and_conflicts_use_real_transactions(demo_client):
    client = demo_client
    document = client.post("/document/", json={
        "project_id": 1, "document_code": "DEMO-NEW", "document_description": "New document",
    })
    assert document.status_code == 200, document.text
    document_id = document.json()["id"]
    assert client.post(
        "/document/", json={"project_id": 1, "document_code": "DEMO-NEW"},
    ).status_code == 409
    assert client.post(f"/document_role/{document_id}/1").status_code == 200
    issue = client.post(f"/issue/{document_id}", json={"date": "2025-03-01"})
    assert issue.status_code == 200
    issue_id = issue.json()["id"]
    assert client.patch(f"/issue/{issue_id}", json={"revision_number": 3}).status_code == 200
    assert client.patch(
        f"/document/{document_id}", json={"document_description": "Edited in the demo"},
    ).status_code == 200
    response = client.get(f"/document_issue/{document_id}")
    assert response.status_code == 200
    aggregate = DocumentIssue.model_validate(response.json())
    assert aggregate.document_description == "Edited in the demo"
    assert aggregate.issue_history[0].revision == "P03"
    assert aggregate.director_in_charge == "AA"
    assert client.delete(f"/document/{document_id}").status_code == 200
    assert client.get(f"/document/{document_id}").status_code == 404
    assert client.get(f"/issue/{issue_id}").status_code == 404
    assert len(client.get("/documents/").json()) == 2


def test_restart_resets_seed_without_modifying_normal_app():
    demo = create_demo_app()
    original_overrides = dict(normal_app.dependency_overrides)
    with TestClient(demo) as client:
        assert client.patch("/document/1", json={"document_description": "Changed"}).status_code == 200
        assert client.get("/document/1").json()["document_description"] == "Changed"
        assert normal_app.dependency_overrides == original_overrides
    assert get_db not in demo.dependency_overrides
    with TestClient(demo) as client:
        assert client.get("/document/1").json()["document_description"] == "Demo equipment schedule"
        assert len(client.get("/documents/").json()) == 2
        assert len(client.get("/project_roles/1/").json()["project_roles"]) == 2
    assert normal_app.dependency_overrides == original_overrides


@pytest.mark.parametrize("configuration", [
    "default", "legacy", "invalid_url", "unsupported_driver", "commit_failure",
])
def test_configured_demo_launcher_serves_seed_without_test_database(tmp_path, configuration):
    """Run the manifest command in a fresh process with the actual package cwd.

    Unlike the normal API tests, this never calls create_all or overrides get_db.
    Cases use api-dev.env unchanged, protect legacy data, and exercise invalid
    normal database configuration. A test-only factory injects a commit failure
    to verify that live HTTP cannot report success for a rolled-back write.
    Only the listening socket is changed to avoid a running user's port 8000.
    """
    root = Path(__file__).resolve().parents[3]
    with (root / "pixi.toml").open("rb") as file:
        task = tomllib.load(file)["tasks"]["demo-api"]
    assert not task.get("depends-on")
    command = shlex.split(task["cmd"])
    assert command[0] == "uvicorn"
    cwd = root / task["cwd"]
    bundled_db = cwd / "src/document_issue_api/app.db"
    watched_files = [bundled_db]
    env = os.environ.copy()
    env.pop("DOCUMENTISSUE_DATABASE_URL", None)
    if configuration == "legacy":
        legacy = tmp_path / "legacy.db"
        with sqlite3.connect(legacy) as db:
            db.execute("CREATE TABLE document (id INTEGER PRIMARY KEY, document_code INTEGER)")
            db.execute("INSERT INTO document VALUES (1, 123)")
        env["DOCUMENTISSUE_DATABASE_URL"] = f"sqlite:///{legacy}"
        watched_files.append(legacy)
    elif configuration == "invalid_url":
        env["DOCUMENTISSUE_DATABASE_URL"] = "not a database URL"
    elif configuration == "unsupported_driver":
        env["DOCUMENTISSUE_DATABASE_URL"] = "unavailable_driver://example"
    elif configuration == "commit_failure":
        # Deliberately fail COMMIT, not flush. TestClient would mask an HTTP
        # response being sent before yield-dependency cleanup; a live socket won't.
        (tmp_path / "commit_failure_demo.py").write_text(textwrap.dedent("""
            from sqlalchemy import select
            from sqlalchemy.exc import IntegrityError
            from sqlalchemy.orm import Session
            from document_issue_api.demo import create_demo_app
            from document_issue_api.models import Project

            original_commit = Session.commit

            def failing_commit(self):
                if self.scalar(select(Project.id).where(Project.project_number == 19999)):
                    raise IntegrityError("COMMIT", {}, RuntimeError("simulated deferred constraint"))
                original_commit(self)

            def create_app():
                Session.commit = failing_commit
                return create_demo_app()
        """))
        command[1] = "commit_failure_demo:create_app"
        command[command.index("--app-dir") + 1] = str(tmp_path)
    hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in watched_files}
    log_path = tmp_path / "demo.log"
    with socket.socket() as listener, log_path.open("w") as log:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        process = subprocess.Popen(
            [sys.executable, "-m", *command, "--fd", str(listener.fileno())],
            cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
            pass_fds=(listener.fileno(),), start_new_session=True,
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=1) as client:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        pytest.fail(log_path.read_text())
                    try:
                        response = client.get("/document_issue/1")
                    except httpx.TransportError:
                        time.sleep(0.1)
                        continue
                    assert response.status_code == 200, response.text + log_path.read_text()
                    aggregate = DocumentIssue.model_validate(response.json())
                    assert aggregate.project_name == "Demo Community Library"
                    assert aggregate.director_in_charge == "AA"
                    assert len(aggregate.issue_history) == 2
                    break
                else:
                    pytest.fail("Demo did not become ready:\n" + log_path.read_text())
                assert client.get("/", follow_redirects=True).status_code == 200
                assert client.get("/document_issue/2").status_code == 200
                assert client.patch("/document/1", json={"notes": ["Live edit"]}).status_code == 200
                assert client.get("/document/1").json()["notes"] == ["Live edit"]
                if configuration == "commit_failure":
                    failed = client.post("/project/", json={"project_number": 19999})
                    assert failed.status_code == 409, failed.text
                    assert len(client.get("/project/").json()) == 1
                    assert client.post("/project/", json={"project_number": 10002}).status_code == 200
                    assert len(client.get("/project/").json()) == 2
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
    for path, digest in hashes.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
