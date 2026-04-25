from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.config import get_settings
from backend.app.core.security import create_admin_token, verify_admin_password, verify_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLoginRequest(BaseModel):
    password: str = Field(min_length=1)


class AdminSession(BaseModel):
    authenticated: bool
    token: str


class AdminStatus(BaseModel):
    authenticated: bool


def require_admin(authorization: Annotated[str | None, Header()] = None) -> bool:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required")

    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    if not verify_admin_token(token, settings.admin_password, settings.admin_token_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    return True


@router.post("/login", response_model=AdminSession)
def login_admin(payload: AdminLoginRequest) -> AdminSession:
    settings = get_settings()
    if not verify_admin_password(payload.password, settings.admin_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong admin password")

    token = create_admin_token(settings.admin_password, settings.admin_token_secret)
    return AdminSession(authenticated=True, token=token)


@router.get("/me", response_model=AdminStatus)
def admin_me(_: bool = Depends(require_admin)) -> AdminStatus:
    return AdminStatus(authenticated=True)
