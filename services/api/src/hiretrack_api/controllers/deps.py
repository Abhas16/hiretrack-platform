"""Dependency injection: builds services per request. The only place that wires layers together."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from hiretrack_api.core.config import ApiSettings
from hiretrack_api.core.database import UnitOfWork, get_session
from hiretrack_api.core.exceptions import AuthenticationError
from hiretrack_api.core.security import TokenService
from hiretrack_api.interviewer.base import Interviewer
from hiretrack_api.models import User
from hiretrack_api.repositories.analytics_repository import AnalyticsRepository
from hiretrack_api.repositories.application_repository import ApplicationRepository
from hiretrack_api.repositories.company_repository import CompanyRepository
from hiretrack_api.repositories.contact_repository import ContactRepository
from hiretrack_api.repositories.interview_repository import InterviewRepository
from hiretrack_api.repositories.note_repository import NoteRepository
from hiretrack_api.repositories.practice_repository import PracticeRepository
from hiretrack_api.repositories.reminder_repository import ReminderRepository
from hiretrack_api.repositories.resume_variant_repository import ResumeVariantRepository
from hiretrack_api.repositories.user_repository import UserRepository
from hiretrack_api.services.analytics_service import AnalyticsService
from hiretrack_api.services.application_service import ApplicationService
from hiretrack_api.services.auth_service import AuthService
from hiretrack_api.services.company_service import CompanyService
from hiretrack_api.services.contact_service import ContactService
from hiretrack_api.services.interview_service import InterviewService
from hiretrack_api.services.note_service import NoteService
from hiretrack_api.services.practice_service import PracticeService
from hiretrack_api.services.reminder_service import ReminderService
from hiretrack_api.services.resume_variant_service import ResumeVariantService

SessionDep = Annotated[Session, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> ApiSettings:
    settings: ApiSettings = request.app.state.settings
    return settings


SettingsDep = Annotated[ApiSettings, Depends(get_settings)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    tokens = TokenService(
        secret=settings.jwt_secret.get_secret_value(),
        issuer=settings.jwt_issuer,
        ttl_minutes=settings.jwt_access_ttl_minutes,
    )
    return AuthService(
        UserRepository(session), UnitOfWork(session), tokens, settings.allow_registration
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    auth: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing bearer token")
    return auth.authenticate(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(
        ApplicationRepository(session),
        CompanyRepository(session),
        ResumeVariantRepository(session),
        UnitOfWork(session),
    )


def get_company_service(session: SessionDep) -> CompanyService:
    return CompanyService(CompanyRepository(session), UnitOfWork(session))


def get_resume_variant_service(session: SessionDep) -> ResumeVariantService:
    return ResumeVariantService(ResumeVariantRepository(session), UnitOfWork(session))


def get_interview_service(session: SessionDep) -> InterviewService:
    return InterviewService(
        InterviewRepository(session), ApplicationRepository(session), UnitOfWork(session)
    )


def get_note_service(session: SessionDep) -> NoteService:
    return NoteService(NoteRepository(session), ApplicationRepository(session), UnitOfWork(session))


def get_contact_service(session: SessionDep) -> ContactService:
    return ContactService(
        ContactRepository(session), CompanyRepository(session), UnitOfWork(session)
    )


def get_reminder_service(session: SessionDep) -> ReminderService:
    return ReminderService(
        ReminderRepository(session), ApplicationRepository(session), UnitOfWork(session)
    )


def get_analytics_service(session: SessionDep) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(session))


def get_practice_service(session: SessionDep, request: Request) -> PracticeService:
    # The interviewer (and its HTTP client to the LLM) is built once at startup and shared.
    interviewer: Interviewer = request.app.state.interviewer
    return PracticeService(
        PracticeRepository(session),
        ApplicationRepository(session),
        interviewer,
        UnitOfWork(session),
    )


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]
ResumeVariantServiceDep = Annotated[ResumeVariantService, Depends(get_resume_variant_service)]
InterviewServiceDep = Annotated[InterviewService, Depends(get_interview_service)]
NoteServiceDep = Annotated[NoteService, Depends(get_note_service)]
ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]
ReminderServiceDep = Annotated[ReminderService, Depends(get_reminder_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
PracticeServiceDep = Annotated[PracticeService, Depends(get_practice_service)]
