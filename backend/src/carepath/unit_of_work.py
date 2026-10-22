"""Transaction boundary for a request.

The unit of work owns one AsyncSession and exposes repositories bound to it.
Callers decide when to commit or roll back; leaving the context manager
without a commit discards the session's pending changes.
"""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from carepath.db import SessionLocal
from carepath.repositories.care_plans import TreatmentPlanRepository
from carepath.repositories.care_tasks import CareTaskRepository
from carepath.repositories.patients import PatientRepository

SessionFactory = async_sessionmaker[AsyncSession] | Callable[[], AsyncSession]


class UnitOfWork(Protocol):
    session: AsyncSession
    patients: PatientRepository
    care_plans: TreatmentPlanRepository
    care_tasks: CareTaskRepository

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork:
    def __init__(
        self,
        session_factory: SessionFactory = SessionLocal,
    ) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None
        self.patients: PatientRepository | None = None
        self.care_plans: TreatmentPlanRepository | None = None
        self.care_tasks: CareTaskRepository | None = None

    async def __aenter__(self) -> Self:
        session = self._session_factory()
        self.session = session
        self.patients = PatientRepository(session)
        self.care_plans = TreatmentPlanRepository(session)
        self.care_tasks = CareTaskRepository(session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = self._require_session()
        try:
            if exc_type is not None:
                await session.rollback()
        finally:
            await session.close()

    async def commit(self) -> None:
        await self._require_session().commit()

    async def rollback(self) -> None:
        await self._require_session().rollback()

    def _require_session(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("unit of work 尚未进入上下文")
        return self.session
