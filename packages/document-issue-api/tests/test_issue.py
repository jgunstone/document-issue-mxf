import pytest
from setup_test_client import client, post_document, post_issue, post_project


@pytest.fixture(autouse=True)
def document_for_issue():
    assert post_project().status_code == 200
    assert post_document().status_code == 200


def delete_issue(issue_id=1):
    return client.delete(f"/issue/{issue_id}")


@pytest.fixture
def post_issue_then_delete():
    r = post_issue()
    assert r.status_code == 200
    id_ = r.json()["id"]
    yield r
    delete_issue(id_)


def test_post_issue(post_issue_then_delete):
    response = post_issue_then_delete
    assert response.status_code == 200
    assert response.json()["revision"] == "P01"


def test_get_issue(post_issue_then_delete):
    response = post_issue_then_delete
    issue_id = response.json()["id"]
    response = client.get(f"/issue/{issue_id}")
    assert response.status_code == 200
    assert response.json()["revision"] == "P01"


def test_patch_issue(post_issue_then_delete):
    response = post_issue_then_delete
    issue_id = response.json()["id"]
    response = client.patch(f"/issue/{issue_id}", json={"revision_number": 2})
    assert response.status_code == 200
    assert response.json()["revision"] == "P02"


def test_delete_issue():
    r = post_issue()
    assert r.status_code == 200
    id_ = r.json()["id"]
    response = client.delete(f"/issue/{id_}")
    assert response.status_code == 200
    assert response.json()["revision"] == "P01"
    response = client.get(f"/issue/{id_}")
    assert response.status_code == 404
