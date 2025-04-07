import os

import pytest
from fastapi.testclient import TestClient

from app import app
from database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def set_working_directory():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


# Test Setup and Fixtures
@pytest.fixture(scope="module")
def test_client():
    Base.metadata.create_all(bind=engine)
    yield client
    # Cleanup: Dispose engine and remove database file
    engine.dispose()
    if os.path.exists("./game.db"):
        os.remove("./game.db")


@pytest.fixture(scope="module")
def jwt_token(test_client):
    response = test_client.post(
        "/user/register",
        json={"username": "testuser", "password": "ValidPass!123"}
    )
    assert response.status_code == 200, f"Failed to register user: {response.json()}"
    return response.json()["jwt_token"]


# GAME ENDPOINT TESTS
def test_game_list_empty(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    response = test_client.get("/game", headers=headers)
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_game_create(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    request_data = {
        "type":                  "maumau",
        "deck_size":             52,
        "number_of_start_cards": 5,
        "gamemode":              "gamemode_classic"
    }
    response = test_client.post("/game", json=request_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "maumau"
    assert data["deck_size"] == 52
    assert data["number_of_start_cards"] == 5
    assert data["max_players"] == min((52 - 10) // 5, 8)
    assert data["gamemode"] == "gamemode_classic"
    assert "id" in data and "code" in data
    assert "created" in data and "updated" in data


def test_game_list_not_available(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    response = test_client.get("/game", headers=headers)
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_game_create_invalid_type(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    response = test_client.post("/game", json={"type": "invalid_type"}, headers=headers)
    assert response.status_code == 422


def test_get_game_by_code(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    request_data = {
        "type":                  "maumau",
        "deck_size":             52,
        "number_of_start_cards": 5,
        "gamemode":              "gamemode_classic"
    }

    create_resp = test_client.post("/game", json=request_data, headers=headers)
    assert create_resp.status_code == 200
    game_data = create_resp.json()
    game_code = game_data["code"]

    get_resp = test_client.get(f"/game/{game_code}", headers=headers)
    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()
    assert retrieved_data["code"] == game_code
    assert retrieved_data["type"] == "maumau"
    assert retrieved_data["deck_size"] == 52
    assert retrieved_data["number_of_start_cards"] == 5
    assert retrieved_data["max_players"] == min((52 - 10) // 5, 8)
    assert retrieved_data["gamemode"] == "gamemode_classic"
    assert "id" in retrieved_data
    assert "created" in retrieved_data
    assert "updated" in retrieved_data


def test_get_game_by_code_invalid_code(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    invalid_code = "123"  # shorter than 6 letters
    resp = test_client.get(f"/game/{invalid_code}", headers=headers)
    assert resp.status_code == 422, resp.text


# USER ENDPOINT TESTS
def test_user_list_not_empty(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    response = test_client.get("/user", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "testuser" in response.json()[0]["username"]


def test_user_create_invalid_username(test_client):
    response = test_client.post(
        "/user/register", json={"username": "ab", "password": "ValidPass!123"}
    )
    assert response.status_code == 422


def test_user_create_invalid_password(test_client):
    response = test_client.post(
        "/user/register", json={"username": "testuser", "password": "short"}
    )
    assert response.status_code == 400


def test_get_user_by_id(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    create_resp = test_client.post(
        "/user/register", json={"username": "uniqueuser", "password": "ValidPass!123"}, headers=headers
    )
    assert create_resp.status_code == 200
    user_data = create_resp.json()
    user_id = user_data["id"]

    get_resp = test_client.get(f"/user/{user_id}", headers=headers)
    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()
    assert retrieved_data["id"] == user_id
    assert retrieved_data["username"] == "uniqueuser"


# Password Change Tests
def test_user_change_password_success(test_client, jwt_token):
    headers = {"Authorization": jwt_token}
    response = client.put(
        "/user/password",
        json={"old_password": "ValidPass!123", "new_password": "NewValidPass!123"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_user_change_password_invalid_current_password(jwt_token):
    headers = {"Authorization": jwt_token}
    response = client.put(
        "/user/password",
        json={"old_password": "InvalidPass", "new_password": "NewValidPass!123"},
        headers=headers,
    )
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid current password"


# Login Tests
def test_user_login_success():
    response = client.post("/user/login", json={"username": "testuser", "password": "NewValidPass!123"})
    assert response.status_code == 200
    data = response.json()
    assert "jwt_token" in data
    assert data["username"] == "testuser"
    assert "id" in data


def test_user_login_invalid_credentials():
    response = client.post("/user/login", json={"username": "testuser", "password": "WrongPassword"})
    assert response.status_code == 406
    assert response.json()["detail"] == "Invalid password"


def test_user_login_nonexistent_user():
    response = client.post("/user/login", json={"username": "nonexistent", "password": "SomePass123"})
    assert response.status_code == 404


# Guest User Tests
def test_guest_login_success():
    response = client.post("/user/guest")
    assert response.status_code == 200
    data = response.json()
    assert "jwt_token" in data
    assert "username" in data
    assert "id" in data


def test_guest_login_with_unnecessary_payload():
    response = client.post("/user/guest", json={"extra_field": "unnecessary"})
    assert response.status_code == 200
    data = response.json()
    assert "jwt_token" in data
    assert "username" in data
    assert "id" in data


# Negative Test Cases
def test_user_change_password_unauthorized():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.put(
        "/user/password",
        json={"old_password": "NewValidPass!123", "new_password": "NewNewValidPass!123"},
        headers=headers
    )
    assert response.status_code == 401  # https://github.com/fastapi/fastapi/discussions/9130


def test_user_login_missing_fields():
    response = client.post("/user/login", json={"username": "testuser"})
    assert response.status_code == 422


def test_user_profile_image_not_found(test_client, jwt_token):
    response = test_client.get("/user/1/profile_picture", headers={"Authorization": jwt_token})
    assert response.status_code == 404


def test_user_profile_image_post(test_client):
    create_resp = test_client.post(
        "/user/register", json={"username": "uniqueuser1", "password": "ValidPass!123"}
    )
    assert create_resp.status_code == 200
    user_data = create_resp.json()
    user_jwt = user_data["jwt_token"]

    post_resp = test_client.put(
        f"/user/profile_picture",
        headers={"Authorization": user_jwt},
        files={"profile_picture": ("icon.png", open("static/icon.png", "rb"), "image/png")}
    )
    assert post_resp.status_code == 200


def test_user_profile_image_get(test_client, jwt_token):
    create_resp = test_client.post(
        "/user/login", json={"username": "uniqueuser1", "password": "ValidPass!123"}
    )
    assert create_resp.status_code == 200
    user_data = create_resp.json()
    user_id = user_data["id"]
    user_jwt = user_data["jwt_token"]

    get_resp = test_client.get(f"/user/{user_id}/profile_picture", headers={"Authorization": user_jwt})
    assert get_resp.status_code == 200
    assert get_resp.headers["content-type"] == "image/png"


def test_user_profile_image_delete(test_client, jwt_token):
    create_resp = test_client.post(
        "/user/login", json={"username": "uniqueuser1", "password": "ValidPass!123"}
    )
    assert create_resp.status_code == 200
    user_data = create_resp.json()
    user_jwt = user_data["jwt_token"]

    delete_resp = test_client.delete(f"/user/profile_picture", headers={"Authorization": user_jwt})
    assert delete_resp.status_code == 200
