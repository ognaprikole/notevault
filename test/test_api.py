from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "pong"
    assert data["project"] == "NoteVault"

import uuid

def test_register_and_duplicate():
    name = "u_" + uuid.uuid4().hex[:8]
    first = client.post("/register", data={"username": name, "password": "1234"})
    assert first.status_code == 200
    assert first.json()["username"] == name

    second = client.post("/register", data={"username": name, "password": "1234"})
    assert second.status_code == 400

def test_notes_without_login():
    response = client.get("/api/notes")
    assert response.status_code == 401

def test_login_wrong_password():
    name = "u_" + uuid.uuid4().hex[:8]
    client.post("/register", data={"username": name, "password": "abcd"})
    bad = client.post("/login", data={"username": name, "password": "wrong"})
    assert bad.status_code == 401


def test_create_and_list_note():
    name = "u_" + uuid.uuid4().hex[:8]
    client.post("/register", data={"username": name, "password": "1234"})
    login = client.post("/login", data={"username": name, "password": "1234"})
    assert login.status_code == 200

    created = client.post("/api/notes", data={"title": "первая", "body": "текст"})
    assert created.status_code == 200
    assert created.json()["title"] == "первая"

    listed = client.get("/api/notes")
    assert listed.status_code == 200
    titles = [n["title"] for n in listed.json()]
    assert "первая" in titles