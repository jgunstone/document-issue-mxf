import pytest
from setup_test_client import client, post_person


def delete_person(person_id=1):
    return client.delete(f"/person/{person_id}")


@pytest.fixture
def post_person_then_delete():
    r = post_person()
    assert r.status_code == 200
    assert isinstance(r.json()["full_name"], str)
    yield r
    id_ = r.json()["id"]
    r1 = delete_person(id_)
    assert r1.status_code == 200


def test_get_person(post_person_then_delete):
    response = post_person_then_delete
    person_id = response.json()["id"]
    response = client.get(f"/person/{person_id}")
    r = response.json()
    assert response.status_code == 200
    assert isinstance(r["initials"], str)


def test_get_people(post_person_then_delete):
    response = post_person_then_delete
    response = client.get("/person/")
    assert response.status_code == 200
    assert isinstance(response.json()[0]["initials"], str)


def test_post_person(post_person_then_delete):
    response = post_person_then_delete
    assert response.status_code == 200
    assert isinstance(response.json()["initials"], str)


def test_patch_person(post_person_then_delete):
    response = post_person_then_delete
    person_id = response.json()["id"]
    response = client.patch(f"/person/{person_id}", json={"name": "JG2", "full_name": "new name"})
    assert response.status_code == 200
    assert response.json()["initials"] == "JG2"


def test_delete_person():
    r = post_person()
    assert r.status_code == 200
    assert isinstance(r.json()["full_name"], str)

    id_ = r.json()["id"]
    r1 = delete_person(id_)

    assert r1.status_code == 200
    response = client.get(f"/person/{id_}")
    assert response.status_code == 404
