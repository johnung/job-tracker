def test_login_with_correct_credentials_returns_token(client, make_user):
    user = make_user(password="secret")
    response = client.post(
        "/auth/login", json={"email": user.email, "password": "secret"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_dummy_password(client):
    response = client.post(
        "/auth/login", json={"email": "dne@example.com", "password": "dummy-password"}
    )
    assert response.status_code == 401


def test_login_with_wrong_password(client, make_user):
    user = make_user(password="secret")
    response = client.post(
        "/auth/login", json={"email": user.email, "password": "password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_wrong_email(client, make_user):
    make_user(email="correct@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "incorrect@example.com", "password": "secret"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_mixed_cased_email(client, make_user):
    make_user(email="me@example.com", password="secret")
    response = client.post(
        "/auth/login", json={"email": "mE@ExAmPlE.CoM", "password": "secret"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_missing_fields(client):
    response = client.post("/auth/login", json={})
    assert response.status_code == 422
