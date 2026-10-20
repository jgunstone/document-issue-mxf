"""Catalogue tests use a standalone app, never the database-backed API app."""

import json
import subprocess
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from document_issue_api.schema_catalogue import SCHEMA_MODELS, router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client


def test_catalogue_lists_stable_names(client):
    response = client.get("/schemas/")
    assert response.status_code == 200
    assert response.json() == sorted(SCHEMA_MODELS)
    assert {
        "Document", "FormatConfiguration", "Project", "Person", "Role",
        "DocumentRole", "PersonRole", "ProjectRoles", "Issue", "DocumentIssue",
        "DocumentIssueClassification", "DocumentIssueV2", "Classification",
        "ProjectCode", "LookupData",
    } <= set(response.json())


@pytest.mark.parametrize("name,model", SCHEMA_MODELS.items())
def test_every_schema_matches_shared_model(client, name, model):
    response = client.get(f"/schemas/{name}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    # A JSON round-trip also normalizes Pydantic's enum-valued schema extras.
    expected = json.loads(json.dumps(model.model_json_schema(by_alias=False, mode="validation")))
    assert response.json() == expected


def test_canonical_fields_and_local_definitions(client):
    schema = client.get("/schemas/DocumentIssue").json()
    properties = schema["properties"]
    assert {"document_code", "document_role", "issue_history", "project_name"} <= properties.keys()
    assert not {"document_name", "roles", "issue", "Project Name"} & properties.keys()
    assert properties["issue_history"]["items"]["$ref"] == "#/$defs/Issue"
    assert "Issue" in schema["$defs"]
    assert "role_name" in schema["$defs"]["DocumentRole"]["properties"]


def test_project_metadata_and_project_code_are_distinct(client):
    metadata = client.get("/schemas/Project").json()["properties"]
    code = client.get("/schemas/ProjectCode").json()["properties"]
    assert "project_number" in metadata
    assert "number" not in metadata
    assert {"code", "description", "number"} <= code.keys()
    assert "project_number" not in code


@pytest.mark.parametrize("name", ["unknown", "document", "document_issue.document.Document", "BaseModel"])
def test_unknown_names_are_not_imported(client, name):
    response = client.get(f"/schemas/{name}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown schema model"}


def test_schema_is_generated_on_request(client, monkeypatch):
    model = SCHEMA_MODELS["Document"]
    monkeypatch.setattr(
        model,
        "model_json_schema",
        lambda **kwargs: {"title": "Generated now", "options": kwargs},
    )
    assert client.get("/schemas/Document").json() == {
        "title": "Generated now",
        "options": {"by_alias": False, "mode": "validation"},
    }


def test_import_does_not_load_database_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import document_issue_api.schema_catalogue; "
            "assert 'document_issue_api.main' not in sys.modules; "
            "assert 'document_issue_api.database' not in sys.modules; "
            "assert 'sqlalchemy' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
