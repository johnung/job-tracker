from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.application import ApplicationStage
from app.models.event import EventKind


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)
    stage: ApplicationStage = ApplicationStage.APPLIED
    applied_on: date | None = None
    posting_url: str | None = Field(default=None, max_length=2048)
    pay_range: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=255)
    went_well: str | None = None
    to_improve: str | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, min_length=1, max_length=255)
    stage: ApplicationStage | None = None
    applied_on: date | None = None
    posting_url: str | None = Field(default=None, max_length=2048)
    pay_range: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=255)
    went_well: str | None = None
    to_improve: str | None = None
    notes: str | None = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    title: str | None
    how_met: str | None
    notes: str | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_on: date
    kind: EventKind
    body: str | None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role: str
    stage: ApplicationStage
    applied_on: date | None
    posting_url: str | None
    pay_range: str | None
    location: str | None
    source: str | None
    went_well: str | None
    to_improve: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationDetail(ApplicationOut):
    contacts: list[ContactOut]
    events: list[EventOut]
