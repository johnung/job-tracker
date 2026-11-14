from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser
from app.models import Application, Event, User
from app.models.application import ApplicationStage
from app.models.event import EventKind
from app.schemas.application import ApplicationCreate, ApplicationDetail, ApplicationOut

router = APIRouter(prefix="/applications", tags=["applications"])


def stage_change_event(
    old_stage: ApplicationStage | None,
    new_stage: ApplicationStage,
    occurred_on: date,
) -> Event:
    body = (
        f"{old_stage} -> {new_stage}" if old_stage else f"Created at stage: {new_stage}"
    )
    return Event(kind=EventKind.STAGE_CHANGE, body=body, occurred_on=occurred_on)


def get_owned_application(db: Session, application_id: int, user: User) -> Application:
    application = db.scalar(
        select(Application).where(
            Application.id == application_id, Application.user_id == user.id
        )
    )
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    return application


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    body: ApplicationCreate, user: CurrentUser, db: Annotated[Session, Depends(get_db)]
):
    application = Application(user_id=user.id, **body.model_dump())
    application.events.append(
        stage_change_event(None, application.stage, body.applied_on or date.today())
    )
    db.add(application)
    db.commit()
    return application


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    stage: ApplicationStage | None = None,
):
    stmt = (
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
    )
    if stage is not None:
        stmt = stmt.where(Application.stage == stage)

    applications = db.scalars(stmt).all()

    return applications


@router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(
    application_id: int, user: CurrentUser, db: Annotated[Session, Depends(get_db)]
):
    return get_owned_application(db, application_id, user)
