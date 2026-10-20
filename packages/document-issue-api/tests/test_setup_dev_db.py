"""Smoke-test seeded data without copying a test database over application data."""


def test_seed_workflow(client):
    project = client.post("/project/", json={"project_number": 1234}).json()
    document = client.post("/document/", json={"project_id": project["id"]})
    assert document.status_code == 200
    issue = client.post(f"/issue/{document.json()['id']}", json={})
    assert issue.status_code == 200
    response = client.get(f"/document_issue/{document.json()['id']}")
    assert response.status_code == 200
    assert len(response.json()["issue"]) == 1
