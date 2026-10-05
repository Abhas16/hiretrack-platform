"""Enumerations stored in the database. Values are stored as strings (VARCHAR + CHECK)."""

from enum import StrEnum


class ApplicationStatus(StrEnum):
    WISHLIST = "WISHLIST"
    APPLIED = "APPLIED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"


class ApplicationSource(StrEnum):
    REFERRAL = "REFERRAL"
    LINKEDIN = "LINKEDIN"
    NAUKRI = "NAUKRI"
    COMPANY_SITE = "COMPANY_SITE"
    GREENHOUSE = "GREENHOUSE"
    LEVER = "LEVER"
    ASHBY = "ASHBY"
    OTHER = "OTHER"


class InterviewKind(StrEnum):
    PHONE_SCREEN = "PHONE_SCREEN"
    HR = "HR"
    TECHNICAL = "TECHNICAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    BEHAVIORAL = "BEHAVIORAL"
    ONSITE = "ONSITE"
    OTHER = "OTHER"


class InterviewOutcome(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReminderKind(StrEnum):
    FOLLOW_UP = "FOLLOW_UP"
    CUSTOM = "CUSTOM"


class ReminderStatus(StrEnum):
    OPEN = "OPEN"
    DONE = "DONE"
    DISMISSED = "DISMISSED"


class ReminderCreatedBy(StrEnum):
    USER = "USER"
    WORKER = "WORKER"


class PracticeStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
