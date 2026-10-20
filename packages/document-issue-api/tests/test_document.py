import pytest
from document_issue import Document, DocumentIssue
from document_issue.enums import DocumentTypeEnum, RoleEnum
from document_issue_api import models


def post(client, path, payload=None, **kwargs):
    response = client.post(path, json=payload, **kwargs)
    assert response.status_code == 200, response.text
    return response.json()


def project_and_document(client, number=1234, **fields):
    project = post(client, "/project/", {"project_number": number, "project_name": f"Project {number}"})
    document = post(client, "/document/", {"project_id": project["id"], **fields})
    return project, document


def test_document_round_trip(client, db):
    _, document = project_and_document(
        client,
        document_name="00001-MXF-XX-XX-SH-M-20003",
        document_type=DocumentTypeEnum.prs.value,
        doc_source="R24",
        notes=["Keep this note"],
        format_configuration={
            "date_string_format": "%Y/%m/%d", "output_author": True, "output_checked_by": True,
        },
    )
    identifier = document["id"]
    assert document["document_name"].startswith("00001-")
    assert document["size"] == "A3"
    assert Document.model_validate(document).format_configuration.output_author is True
    assert client.get(f"/document/{identifier}").json() == document
    assert client.get("/documents/").json() == [document]

    response = client.patch(
        f"/document/{identifier}",
        json={"document_description": "Updated", "format_configuration": {"output_author": False}},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["document_name"] == document["document_name"]
    assert updated["format_configuration"] == {
        "date_string_format": "%Y/%m/%d", "output_author": False, "output_checked_by": True,
    }
    assert updated["notes"] == ["Keep this note"]
    assert client.get(f"/document/{identifier}").json() == updated
    stored = db.get(models.Document, identifier)
    assert stored.document_type == DocumentTypeEnum.prs.value
    assert stored.output_author is False
    assert stored.output_checked_by is True
    assert client.delete(f"/document/{identifier}").status_code == 200
    assert client.get(f"/document/{identifier}").status_code == 404


@pytest.mark.parametrize("patch", [
    {"document_code": None},
    {"format_configuration": None},
    {"format_configuration": {"output_author": None}},
    {"document_type": "unknown"},
    {"project_id": 999},
])
def test_invalid_patch_does_not_change_document(client, patch):
    _, document = project_and_document(client)
    assert client.patch(f"/document/{document['id']}", json=patch).status_code == 422
    assert client.get(f"/document/{document['id']}").json() == document


def test_document_uniqueness_and_missing_relationships(client):
    project, document = project_and_document(client)
    assert client.post("/document/", json={"project_id": project["id"]}).status_code == 409
    # Same code is valid in another project, and the failed transaction was rolled back.
    _, second = project_and_document(client, number=2345)
    assert second["document_name"] == document["document_name"]
    assert client.post("/document/", json={"project_id": 999}).status_code == 404
    assert client.post("/issue/999", json={}).status_code == 404
    for method in (client.get, client.delete):
        assert method("/document/999").status_code == 404
    assert client.get("/document_issue/999").status_code == 404


def test_aggregate_uses_correct_project_assignments(client):
    first_project, first = project_and_document(client)
    second_project, second = project_and_document(client, number=2345)
    role = post(client, "/role/", {"role_name": RoleEnum.director_in_charge.value})
    for project, initials in ((first_project, "AAA"), (second_project, "BBB")):
        person = post(client, "/person/", {"initials": initials, "full_name": initials})
        post(client, f"/project_role/{project['id']}/{role['id']}", params={"person_id": person["id"]})
    for document in (first, second):
        selection = post(client, f"/document_role/{document['id']}/{role['id']}")
        assert selection["document_id"] == document["id"]
        assert selection["project_id"] == document["project_id"]
        assert client.get(f"/document_roles/{document['id']}/").json() == [selection]

    issue = post(client, f"/issue/{second['id']}", {"revision_number": 3, "date": "2025-02-01"})
    response = client.get(f"/document_issue/{second['id']}")
    assert response.status_code == 200, response.text
    aggregate = DocumentIssue.model_validate(response.json())
    assert aggregate.project_number == 2345
    assert aggregate.document_code == second["document_name"]
    assert [(role.role_name, role.initials) for role in aggregate.document_role] == [
        (RoleEnum.director_in_charge.value, "BBB"),
    ]
    assert aggregate.issue_history[0].revision == issue["revision"]
    assert len(aggregate.issue_history) == 1
    # Assignments in active use cannot be removed; project deletion cascades its documents.
    assert client.delete(f"/project_role/{second_project['id']}/{role['id']}").status_code == 409
    assert client.delete(f"/role/{role['id']}").status_code == 409
    assert client.delete(f"/project/{second_project['id']}").status_code == 200
    assert client.get(f"/issue/{issue['id']}").status_code == 404
    assert client.get(f"/document/{first['id']}").status_code == 200


def test_role_selection_requires_same_project(client):
    project, document = project_and_document(client)
    other, _ = project_and_document(client, number=2345)
    role = post(client, "/role/", {"role_name": RoleEnum.director_in_charge.value})
    post(client, f"/project_role/{other['id']}/{role['id']}")
    assert client.post(f"/document_role/{document['id']}/{role['id']}").status_code == 409
    assert client.post(f"/project_role/{project['id']}/999").status_code == 404
    assert client.get("/project_roles/999/").status_code == 404
    assert client.get("/document_roles/999/").status_code == 404


@pytest.mark.parametrize("custom_role", [False, True])
def test_incomplete_roles_are_explicit_conflicts(client, custom_role):
    project, document = project_and_document(client)
    role = post(client, "/role/", {
        "role_name": "Custom role" if custom_role else RoleEnum.director_in_charge.value,
    })
    params = {}
    if custom_role:
        person = post(client, "/person/", {"initials": "ABC", "full_name": "A Person"})
        params["person_id"] = person["id"]
    post(client, f"/project_role/{project['id']}/{role['id']}", params=params)
    post(client, f"/document_role/{document['id']}/{role['id']}")
    assert client.get(f"/document_issue/{document['id']}").status_code == 409
    assert client.delete(f"/document_role/{document['id']}/{role['id']}").status_code == 200
    assert client.delete(f"/project_role/{project['id']}/{role['id']}").status_code == 200
    aggregate = DocumentIssue.model_validate(client.get(f"/document_issue/{document['id']}").json())
    assert aggregate.document_role[0].initials == "DR"
    assert aggregate.issue_history == []


def test_openapi_and_catalogue_expose_domain_models(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    document_schema = schemas.get("DocumentBasePost-Input", schemas.get("DocumentBasePost"))
    assert "format_configuration" in document_schema["properties"]
    assert client.get("/schemas/Document").json() == Document.model_json_schema(by_alias=False)


def test_legacy_selection_without_project_assignment_can_be_deleted(client, db):
    _, document = project_and_document(client)
    role = post(client, "/role/", {"role_name": RoleEnum.director_in_charge.value})
    db.add(models.DocumentRole(document_id=document["id"], role_id=role["id"]))
    db.commit()
    assert client.get(f"/document_issue/{document['id']}").status_code == 409
    response = client.delete(f"/document_role/{document['id']}/{role['id']}")
    assert response.status_code == 200, response.text
    assert response.json() == {"document_id": document["id"], "role_id": role["id"]}
    assert client.get(f"/document_roles/{document['id']}/").json() == []
    assert client.get(f"/document_issue/{document['id']}").status_code == 200
