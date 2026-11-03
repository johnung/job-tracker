from datetime import timedelta

from fastapi import APIRouter

from app.deps import CurrentUser
from app.main import app
from app.security import create_access_token

router = APIRouter()


@router.get("/test-only/me")
def me(user: CurrentUser):
    return {"id": user.id}


app.include_router(router)


def test_valid_token_returns_user(client, make_user):
    user = make_user()
    token = create_access_token(user.id)
    response = client.get("/test-only/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["id"] == user.id


def test_missing_header_returns_401(client):
    response = client.get("/test-only/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_scheme_returns_401(client, make_user):
    user = make_user()
    token = create_access_token(user.id)
    response = client.get("/test-only/me", headers={"Authorization": f"Basic {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_garbage_token_returns_401(client):
    response = client.get("/test-only/me", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_expired_token_returns_401(client, make_user):
    user = make_user()
    token = create_access_token(user.id, expires_delta=timedelta(seconds=-1))
    response = client.get("/test-only/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_nonexistent_user_token_returns_401(client, make_user, db_session):
    user = make_user()
    token = create_access_token(user.id)
    db_session.delete(user)
    db_session.commit()
    response = client.get("/test-only/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
