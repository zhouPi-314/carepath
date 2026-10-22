from __future__ import annotations

import pytest

from carepath.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_repositories_scope_queries(client) -> None:
    async with SqlAlchemyUnitOfWork() as uow:
        patient = await uow.patients.get_by_user("user-patient")
        assert patient is not None and patient.id == "patient-main"

        doctor_plans = await uow.care_plans.list_for_doctor("user-doctor")
        assert doctor_plans
        assert all(plan.doctor_id == "user-doctor" for plan in doctor_plans)

        assert await uow.care_plans.patient_is_assigned("patient-main", "org-hospital-a")
        assert not await uow.care_plans.patient_is_assigned(
            "patient-main", "org-hospital-b"
        )

        tasks = await uow.care_tasks.list_for_patient("patient-main")
        assert tasks
        assert [task.due_at for task in tasks] == sorted(task.due_at for task in tasks)


@pytest.mark.asyncio
async def test_unit_of_work_commit_persists_and_rollback_discards(client) -> None:
    async with SqlAlchemyUnitOfWork() as uow:
        task = (await uow.care_tasks.list_for_patient("patient-main"))[0]
        task_id = task.id
        task.title = "UoW 提交测试"
        await uow.commit()

    async with SqlAlchemyUnitOfWork() as uow:
        stored = await uow.care_tasks.get(task_id)
        assert stored is not None and stored.title == "UoW 提交测试"

    async with SqlAlchemyUnitOfWork() as uow:
        task = await uow.care_tasks.get(task_id)
        assert task is not None
        task.title = "UoW 回滚测试"
        await uow.rollback()

    async with SqlAlchemyUnitOfWork() as uow:
        stored = await uow.care_tasks.get(task_id)
        assert stored is not None and stored.title == "UoW 提交测试"


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_when_context_raises(client) -> None:
    async with SqlAlchemyUnitOfWork() as uow:
        task = (await uow.care_tasks.list_for_patient("patient-main"))[0]
        task_id = task.id
        task.title = "不应保留"

    async with SqlAlchemyUnitOfWork() as uow:
        stored = await uow.care_tasks.get(task_id)
        assert stored is not None and stored.title != "不应保留"
