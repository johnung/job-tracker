# Import every model here so Alembic autogenerate can see it.
from app.models.application import Application
from app.models.contact import Contact
from app.models.event import Event
from app.models.job_run import JobRun
from app.models.user import User

__all__ = ["Application", "Contact", "Event", "JobRun", "User"]
