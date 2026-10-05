from fastapi import APIRouter, status

from hiretrack_api.controllers.deps import AuthServiceDep, CurrentUser
from hiretrack_api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, auth: AuthServiceDep) -> UserRead:
    return UserRead.model_validate(auth.register(body))


@router.post("/login")
def login(body: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    token, expires_in = auth.login(body.email, body.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me")
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
