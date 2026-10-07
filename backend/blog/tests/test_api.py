import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def token(client):
    get_user_model().objects.create_user("alice", password="pass12345")
    r = client.post("/api/token/", {"username": "alice", "password": "pass12345"})
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data
    return r.data["access"]


def test_health(client):
    r = client.get("/health/")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_readiness(client):
    r = client.get("/readiness/")
    assert r.status_code == 200 and r.json() == {"status": "ready"}


def test_list_posts_public(client):
    assert client.get("/posts/").status_code == 200


def test_create_post_requires_auth(client):
    r = client.post("/posts/", {"title": "t", "content": "c"})
    assert r.status_code == 401


def test_create_post_and_comment(client, token):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    r = client.post("/posts/", {"title": "Hello", "content": "World"})
    assert r.status_code == 201
    pid = r.data["id"]
    assert r.data["author"] == "alice"

    r = client.post(f"/posts/{pid}/comments/", {"content": "Nice"})
    assert r.status_code == 201

    client.credentials()
    r = client.get(f"/posts/{pid}/comments/")
    assert r.status_code == 200 and len(r.json()) == 1


def test_comment_requires_auth(client, token):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    pid = client.post("/posts/", {"title": "a", "content": "b"}).data["id"]
    client.credentials()
    assert client.post(f"/posts/{pid}/comments/", {"content": "x"}).status_code == 401


def test_comments_missing_post_404(client):
    assert client.get("/posts/999/comments/").status_code == 404
