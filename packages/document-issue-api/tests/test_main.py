from setup_test_client import client


def test_app_exists():
    assert client
    assert client.get("/openapi.json").status_code == 200
