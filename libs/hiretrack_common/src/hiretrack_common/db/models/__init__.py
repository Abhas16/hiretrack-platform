"""All ORM models. Importing this package registers every table on Base.metadata."""

from hiretrack_common.db.models.application import Application, ApplicationStatusHistory
from hiretrack_common.db.models.company import Company
from hiretrack_common.db.models.contact import Contact
from hiretrack_common.db.models.interview import Interview
from hiretrack_common.db.models.note import Note
from hiretrack_common.db.models.practice import PracticeSession, PracticeTurn
from hiretrack_common.db.models.reminder import Reminder
from hiretrack_common.db.models.resume_variant import ResumeVariant
from hiretrack_common.db.models.user import User

__all__ = [
    "Application",
    "ApplicationStatusHistory",
    "Company",
    "Contact",
    "Interview",
    "Note",
    "PracticeSession",
    "PracticeTurn",
    "Reminder",
    "ResumeVariant",
    "User",
]
