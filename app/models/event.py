import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EventKind(enum.StrEnum):
    NOTE = "note"
    STAGE_CHANGE = "stage_change"
    INTERVIEW = "interview"
    EMAIL = "email"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_application_id_occurred_on", "application_id", "occurred_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE")
    )
    occurred_on: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    kind: Mapped[EventKind] = mapped_column(
        Enum(
            EventKind,
            name="event_kind",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=EventKind.NOTE,
    )
    body: Mapped[str | None] = mapped_column(Text)
