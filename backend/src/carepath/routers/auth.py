from __future__ import annotations

import secrets

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.db import get_db
from carepath.deps import CurrentUser, get_current_user, issue_tokens
from carepath.models import Organization, User
from carepath.schemas import LoginRequest, LoginResponse, RefreshRequest, UserOut
from carepath.security import verify_password, verify_token
from carepath.settings import get_settings

router = APIRouter(prefix="/auth", tags=["认证"])


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "carepath_access",
        access,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.access_token_minutes * 60,
        path="/",
    )
    response.set_cookie(
        "carepath_refresh",
        refresh,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )


async def _user_out(db: AsyncSession, user: User) -> UserOut:
    organization = (
        await db.get(Organization, user.organization_id)
        if user.organization_id
        else None
    )
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=organization.name if organization else None,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )
    csrf_token = secrets.token_urlsafe(24)
    access, refresh = issue_tokens(user, csrf_token)
    _set_auth_cookies(response, access, refresh)
    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
        csrf_token=csrf_token,
        user=await _user_out(db, user),
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    payload: RefreshRequest | None,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    token = payload.refresh_token if payload and payload.refresh_token else request.cookies.get(
        "carepath_refresh"
    )
    if not token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    try:
        claims = verify_token(
            token,
            secret_key=get_settings().secret_key,
            expected_type="refresh",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="刷新令牌无效") from exc
    user = await db.get(User, claims["sub"])
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="账号不可用")
    csrf_token = secrets.token_urlsafe(24)
    access, new_refresh = issue_tokens(user, csrf_token)
    _set_auth_cookies(response, access, new_refresh)
    return LoginResponse(
        access_token=access,
        refresh_token=new_refresh,
        csrf_token=csrf_token,
        user=await _user_out(db, user),
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie("carepath_access", path="/")
    response.delete_cookie("carepath_refresh", path="/api/v1/auth")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    return await _user_out(db, current.user)
