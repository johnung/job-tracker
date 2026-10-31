import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture
def db_session():
    """A session whose work is rolled back after each test.

    The outer transaction is never committed; commits inside the code under
    test become savepoints (join_transaction_mode="create_savepoint").
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """TestClient whose routes use the rolled-back test session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    """Factory: make_user(email=..., password=...) -> persisted User."""

    def _make_user(email="me@example.com", password="correct-password", name=None):
        user = User(email=email, password_hash=hash_password(password), name=name)
        db_session.add(user)
        db_session.commit()
        return user

    return _make_user
