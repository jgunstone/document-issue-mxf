"""Regression coverage for partial updates and resource error semantics."""

import pytest

from document_issue_api import models


def test_patch_preserves_domain_input_normalizers(client):
    project = client.post("/project/", json={}).json()
    document = client.post("/document/", json={"project_id": project["id"]}).json()
    issue = client.post(f"/issue/{document['id']}", json={}).json()
    response = client.patch(
        f"/issue/{issue['id']}", json={"issue_format": "ea", "date": "01 Jan 24"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["issue_format"] == "Sent as Email attachment"
    assert response.json()["date"] == "2024-01-01"


@pytest.mark.parametrize(("resource", "payload", "field"), [
    ("person", {"initials": "AB", "full_name": "A Person"}, "initials"),
    ("project", {"project_number": 1234}, "project_number"),
])
def test_patch_rejects_null_before_domain_normalizers(client, resource, payload, field):
    row = client.post(f"/{resource}/", json=payload).json()
    response = client.patch(f"/{resource}/{row['id']}", json={field: None})
    assert response.status_code == 422


def create(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def create_issue(client):
    project = create(client, "/project/", {"project_number": 1234})
    document = create(client, "/document/", {"project_id": project["id"]})
    return create(client, f"/issue/{document['id']}", {})


def test_person_partial_name_and_alias(client):
    person = create(client, "/person/", {"initials": "AB", "full_name": "Alice Brown"})
    path = f"/person/{person['id']}"
    response = client.patch(path, json={"full_name": "Alice Blue"})
    assert response.status_code == 200
    assert response.json() == {**person, "full_name": "Alice Blue"}
    response = client.patch(path, json={"name": "ABCDEmore"})
    assert response.status_code == 200
    assert response.json()["initials"] == "ABCDE"
    assert response.json()["full_name"] == "Alice Blue"
    assert client.get(path).json() == response.json()


@pytest.mark.parametrize(
    ("resource", "payload", "field"),
    [
        ("person", {"initials": "AB", "full_name": "Alice Brown"}, "full_name"),
        ("project", {"project_number": 1234}, "project_name"),
        ("role", {"role_name": "Engineer"}, "is_archived"),
    ],
)
def test_patch_rejects_new_nullability(client, resource, payload, field):
    original = create(client, f"/{resource}/", payload)
    path = f"/{resource}/{original['id']}"
    response = client.patch(path, json={field: None})
    assert response.status_code == 422
    assert client.get(path).json() == original


def test_project_partial_update_preserves_stored_defaults_and_aliases(client):
    project = create(
        client,
        "/project/",
        {
            "project_number": 4321,
            "project_code": "CUSTOM",
            "project_name": "Original",
            "client_name": "Client",
            "project_address": "An address",
        },
    )
    path = f"/project/{project['id']}"
    response = client.patch(path, json={"Project Name": "Renamed"})
    assert response.status_code == 200
    assert response.json() == {**project, "project_name": "Renamed"}
    assert client.get(path).json() == response.json()
    assert client.patch(path, json={}).json() == response.json()


def test_role_partial_update_preserves_archive_flag(client):
    role = create(client, "/role/", {"role_name": "Engineer", "is_archived": True})
    path = f"/role/{role['id']}"
    response = client.patch(path, json={"role_description": "Updated"})
    assert response.status_code == 200
    assert response.json() == {**role, "role_description": "Updated"}
    assert client.get(path).json() == response.json()


def test_issue_patch_persists_derived_fields(client, db):
    issue = create_issue(client)
    path = f"/issue/{issue['id']}"
    status = "A1 - Approved - C - Contractual - Approved for construction"
    response = client.patch(path, json={"status_revision": status, "revision_number": 7})
    assert response.status_code == 200
    expected = {
        "revision": "C07",
        "status_code": "A1",
        "status_description": "Approved for construction",
    }
    for field, value in expected.items():
        assert response.json()[field] == value
    assert client.get(path).json() == response.json()

    # Inspect storage too: response-model validation can hide stale derived fields.
    db.expire_all()
    stored = db.get(models.Issue, issue["id"])
    for field, value in expected.items():
        assert getattr(stored, field) == value

    response = client.patch(path, json={"revision_number": 8})
    assert response.status_code == 200
    assert response.json()["revision"] == "C08"
    assert response.json()["status_revision"] == status
    assert client.get(path).json() == response.json()
    db.expire_all()
    assert db.get(models.Issue, issue["id"]).revision == "C08"


def test_issue_invalid_patch_leaves_original_unchanged(client):
    issue = create_issue(client)
    path = f"/issue/{issue['id']}"
    for patch in ({"status_revision": "invalid"}, {"revision_number": None}):
        assert client.patch(path, json=patch).status_code == 422
        assert client.get(path).json() == issue


@pytest.mark.parametrize("resource", ["person", "project", "role", "issue"])
@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_resources_and_invalid_ids(client, resource, method):
    request = getattr(client, method)
    kwargs = {"json": {}} if method == "patch" else {}
    assert request(f"/{resource}/999", **kwargs).status_code == 404
    assert request(f"/{resource}/not-an-id", **kwargs).status_code == 422


def test_issue_requires_existing_document(client):
    assert client.post("/issue/999", json={}).status_code == 404
    assert client.post("/issue/not-an-id", json={}).status_code == 422
