from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from carepath.db import get_db
from carepath.models import User
from carepath.policies import Principal
from carepath.security import create_access_token, create_refresh_token, verify_token
from carepath.settings import get_settings
from carepath.unit_of_work import SqlAlchemyUnitOfWork


@dataclass(frozen=True)
class CurrentUser:
    user: User
    claims: dict

    @property
    def principal(self) -> Principal:
        return Principal(
            user_id=self.user.id,
            role=self.user.role,
            organization_id=self.user.organization_id,
        )


def issue_tokens(user: User, csrf_token: str) -> tuple[str, str]:
    settings = get_settings()
    access = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        secret_key=settings.secret_key,
        expires_delta=timedelta(minutes=settings.access_token_minutes),
        csrf_token=csrf_token,
    )
    refresh = create_refresh_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
        secret_key=settings.secret_key,
        expires_delta=timedelta(days=settings.refresh_token_days),
    )
    return access, refresh


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    carepath_access: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    used_cookie = False
    token = carepath_access
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        used_cookie = False
    elif carepath_access:
        used_cookie = True
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    try:
        claims = verify_token(
            token,
            secret_key=get_settings().secret_key,
            expected_type="access",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效",
        ) from exc

    if (
        used_cookie
        and request.method not in {"GET", "HEAD", "OPTIONS"}
        and (not x_csrf_token or x_csrf_token != claims.get("csrf"))
    ):
        raise HTTPException(status_code=403, detail="CSRF 校验失败")

    user = await db.get(User, claims.get("sub"))
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号不可用")
    return CurrentUser(user=user, claims=claims)


def require_roles(*roles: str):
    async def dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.user.role not in roles:
            raise HTTPException(status_code=403, detail="当前角色无权执行该操作")
        return current

    return dependency


async def get_unit_of_work() -> AsyncIterator[SqlAlchemyUnitOfWork]:
    async with SqlAlchemyUnitOfWork() as unit_of_work:
        yield unit_of_work


def utcnow() -> datetime:
    return datetime.now(UTC)
