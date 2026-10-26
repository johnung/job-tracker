import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ApplicationStage(enum.StrEnum):
    WISHLIST = "wishlist"
    APPLIED = "applied"
    SCREEN = "screen"
    TECHNICAL = "technical"
    ONSITE = "onsite"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_user_id_stage", "user_id", "stage"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    company: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    stage: Mapped[ApplicationStage] = mapped_column(
        Enum(
            ApplicationStage,
            name="application_stage",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ApplicationStage.APPLIED,
    )
    applied_on: Mapped[date | None] = mapped_column(Date)
    posting_url: Mapped[str | None] = mapped_column(String(2048))
    pay_range: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(255))
    went_well: Mapped[str | None] = mapped_column(Text)
    to_improve: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
