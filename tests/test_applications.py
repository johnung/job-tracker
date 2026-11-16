from datetime import UTC, date, datetime

from sqlalchemy import select

from app.models import Contact, Event
from app.models.application import ApplicationStage
from app.models.event import EventKind


def test_create_application_returns_created_application(
    client, make_user, auth_headers
):
    user = make_user()
    response = client.post(
        "/applications",
        json={"company": "Acme", "role": "Backend Engineer"},
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["company"] == "Acme"
    assert body["role"] == "Backend Engineer"
    assert body["stage"] == "applied"


def test_create_application_writes_first_event(
    client, make_user, auth_headers, db_session
):
    user = make_user()
    response = client.post(
        "/applications",
        json={
            "company": "Acme",
            "role": "Backend Engineer",
            "applied_on": "2026-10-31",
        },
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    body = response.json()
    events = db_session.scalars(
        select(Event).where(Event.application_id == body["id"])
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.kind == EventKind.STAGE_CHANGE
    assert event.body == "Created at stage: applied"
    assert event.occurred_on == date(2026, 10, 31)


def test_create_application_without_applied_on_dates_event_today(
    client, make_user, auth_headers, db_session
):
    user = make_user()
    response = client.post(
        "/applications",
        json={
            "company": "Acme",
            "role": "Backend Engineer",
        },
        headers=auth_headers(user),
    )
    assert response.status_code == 201
    body = response.json()
    events = db_session.scalars(
        select(Event).where(Event.application_id == body["id"])
    ).all()
    event = events[0]
    assert event.occurred_on == date.today()


def test_create_application_without_company_returns_422(
    client, make_user, auth_headers
):
    user = make_user()
    response = client.post(
        "/applications", json={"role": "Backend Engineer"}, headers=auth_headers(user)
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    error = errors[0]
    assert error["loc"] == ["body", "company"]
    assert error["type"] == "missing"


def test_create_application_with_unknown_stage_returns_422(
    client, make_user, auth_headers
):
    user = make_user()
    response = client.post(
        "/applications",
        json={"company": "Acme", "role": "Backend Engineer", "stage": "not_a_stage"},
        headers=auth_headers(user),
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    error = errors[0]
    assert error["loc"] == ["body", "stage"]
    assert error["type"] == "enum"


def test_create_application_without_token_returns_401(client):
    response = client.post(
        "/applications", json={"company": "Acme", "role": "Backend Engineer"}
    )
    assert response.status_code == 401


def test_list_applications_returns_only_your_own(
    client, make_user, make_application, auth_headers
):
    user = make_user()
    other_user = make_user(email="other@email.com")

    make_application(user, company="me")
    make_application(other_user, company="other")

    response = client.get("/applications", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    companies = [application["company"] for application in body]
    assert companies == ["me"]


def test_list_applications_orders_newest_first(
    client, make_user, make_application, auth_headers
):
    user = make_user()

    make_application(
        user, company="Newer", created_at=datetime(2026, 11, 13, tzinfo=UTC)
    )
    make_application(
        user, company="Older", created_at=datetime(2026, 11, 11, tzinfo=UTC)
    )

    response = client.get("/applications", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    companies = [application["company"] for application in body]
    assert companies == ["Newer", "Older"]


def test_list_applications_filters_by_stage(
    client, make_user, make_application, auth_headers
):
    user = make_user()
    make_application(user, company="screen", stage=ApplicationStage.SCREEN)
    make_application(user, company="rejected", stage=ApplicationStage.REJECTED)

    response = client.get(
        "/applications", params={"stage": "screen"}, headers=auth_headers(user)
    )
    assert response.status_code == 200
    body = response.json()
    companies = [application["company"] for application in body]
    assert companies == ["screen"]


def test_get_application_includes_contacts_and_events(
    client, make_user, make_application, auth_headers, db_session
):
    user = make_user()
    application = make_application(user, company="Acme")
    application.contacts.append(Contact(name="Jane Recruiter"))
    application.events.append(Event(kind=EventKind.INTERVIEW))
    db_session.commit()

    response = client.get(f"/applications/{application.id}", headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()

    events = body["events"]
    assert len(events) == 1
    event = events[0]
    assert event["kind"] == "interview"

    contacts = body["contacts"]
    assert len(contacts) == 1
    contact = contacts[0]
    assert contact["name"] == "Jane Recruiter"


def test_get_application_another_user_returns_404(
    client, make_user, auth_headers, make_application
):
    user = make_user()
    other_user = make_user(email="other@email.com")

    other_app = make_application(other_user, company="other")
    response = client.get(f"/applications/{other_app.id}", headers=auth_headers(user))

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_get_application_with_missing_id_returns_404(client, make_user, auth_headers):
    user = make_user()
    response = client.get("/applications/-1", headers=auth_headers(user))
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"
