from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from carepath.db import SessionLocal
from carepath.models import (
    Alert,
    CaregiverGrant,
    CarePlanTemplate,
    CareTask,
    DrugProduct,
    MedicationLog,
    MedicationSchedule,
    Observation,
    OfficialDataset,
    Organization,
    PatientConsent,
    PatientProfile,
    ReviewCase,
    SupplyCapacityReport,
    TreatmentPlan,
    User,
)
from carepath.security import hash_password

DEMO_PASSWORD = "CarePath123!"


async def seed_database() -> None:
    async with SessionLocal() as db:
        existing = await db.scalar(select(User.id).limit(1))
        if existing:
            return

        password_hash = hash_password(DEMO_PASSWORD)
        hospital_a = Organization(
            id="org-hospital-a",
            name="海州市第一人民医院",
            type="HOSPITAL",
            region_code="310000",
            verified=True,
        )
        hospital_b = Organization(
            id="org-hospital-b",
            name="海州市康复医院",
            type="HOSPITAL",
            region_code="310000",
            verified=True,
        )
        hospital_c = Organization(
            id="org-hospital-c",
            name="海州市社区医疗中心",
            type="COMMUNITY",
            region_code="310000",
            verified=False,
        )
        regulator = Organization(
            id="org-regulator",
            name="海州市卫生健康数据平台（沙箱）",
            type="REGULATOR",
            region_code="310000",
            verified=True,
        )
        pharma = Organization(
            id="org-pharma",
            name="华康示范药业有限公司（虚构）",
            type="PHARMA",
            region_code="310000",
            verified=True,
        )
        db.add_all([hospital_a, hospital_b, hospital_c, regulator, pharma])

        patient_user = User(
            id="user-patient",
            username="patient",
            password_hash=password_hash,
            display_name="陈安",
            role="PATIENT",
            phone_masked="138****1024",
            seeded_demo=True,
        )
        caregiver_user = User(
            id="user-caregiver",
            username="caregiver",
            password_hash=password_hash,
            display_name="陈宁",
            role="CAREGIVER",
            phone_masked="139****2048",
            seeded_demo=True,
        )
        doctor_user = User(
            id="user-doctor",
            username="doctor",
            password_hash=password_hash,
            display_name="林医生",
            role="DOCTOR",
            organization_id=hospital_a.id,
            seeded_demo=True,
        )
        doctor_b = User(
            id="user-doctor-b",
            username="doctor_b",
            password_hash=password_hash,
            display_name="周医生",
            role="DOCTOR",
            organization_id=hospital_b.id,
            seeded_demo=True,
        )
        doctor_c = User(
            id="user-doctor-c",
            username="doctor_c",
            password_hash=password_hash,
            display_name="顾医生",
            role="DOCTOR",
            organization_id=hospital_c.id,
            seeded_demo=True,
        )
        hospital_admin = User(
            id="user-hospital",
            username="hospital",
            password_hash=password_hash,
            display_name="医院管理员",
            role="HOSPITAL_ADMIN",
            organization_id=hospital_a.id,
            seeded_demo=True,
        )
        regulator_user = User(
            id="user-regulator",
            username="regulator",
            password_hash=password_hash,
            display_name="监管审核员",
            role="REGULATOR",
            organization_id=regulator.id,
            seeded_demo=True,
        )
        pharma_user = User(
            id="user-pharma",
            username="pharma",
            password_hash=password_hash,
            display_name="药企计划员",
            role="PHARMA",
            organization_id=pharma.id,
            seeded_demo=True,
        )
        admin_user = User(
            id="user-admin",
            username="admin",
            password_hash=password_hash,
            display_name="系统管理员",
            role="SYSTEM_ADMIN",
            seeded_demo=True,
        )
        db.add_all(
            [
                patient_user,
                caregiver_user,
                doctor_user,
                doctor_b,
                doctor_c,
                hospital_admin,
                regulator_user,
                pharma_user,
                admin_user,
            ]
        )
        await db.flush()

        patient = PatientProfile(
            id="patient-main",
            user_id=patient_user.id,
            display_name="陈安",
            record_number="DEMO-2026-0001",
            region_code="310000",
        )
        db.add(patient)
        db.add(
            CaregiverGrant(
                patient_id=patient.id,
                caregiver_user_id=caregiver_user.id,
                scopes=[
                    "tasks:read",
                    "tasks:complete",
                    "medications:read",
                    "appointments:read",
                    "observations:read",
                    "observations:write",
                ],
                active=True,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )

        hypertension = CarePlanTemplate(
            id="template-hypertension",
            name="高血压长期随访",
            condition_focus="慢病管理",
            version=1,
            status="PUBLISHED",
            content={
                "summary": "14 天启动期与持续月度随访的演示模板",
                "phases": [
                    {"name": "启动期", "durationDays": 14},
                    {"name": "稳定随访期", "durationDays": 90},
                ],
                "tasks": [
                    {
                        "title": "每日晨间血压记录",
                        "description": "静坐 5 分钟后测量并记录收缩压和舒张压。",
                        "category": "OBSERVATION",
                        "dueAfterDays": 1,
                    },
                    {
                        "title": "完成用药核对",
                        "description": "核对药盒与计划，不自行调整剂量。",
                        "category": "SELF_CARE",
                        "dueAfterDays": 3,
                    },
                    {
                        "title": "复诊预约确认",
                        "description": "确认下一次门诊时间。",
                        "category": "APPOINTMENT",
                        "dueAfterDays": 14,
                    },
                ],
                "observations": [
                    {"type": "BLOOD_PRESSURE", "unit": "mmHg", "frequency": "DAILY"}
                ],
                "medications": [
                    {
                        "drugName": "示例降压片",
                        "approvalNumber": "国药准字H20260001",
                        "doseText": "1 片",
                        "frequencyText": "每日一次",
                    }
                ],
                "alertRules": [
                    {"type": "TASK_OVERDUE", "thresholdHours": 24, "severity": "MEDIUM"}
                ],
            },
            created_by=doctor_user.id,
        )
        recovery = CarePlanTemplate(
            id="template-recovery",
            name="术后 30 天康复",
            condition_focus="出院康复",
            version=1,
            status="PUBLISHED",
            content={
                "summary": "伤口观察、复诊和活动恢复的演示模板",
                "phases": [{"name": "术后观察期", "durationDays": 30}],
                "tasks": [
                    {
                        "title": "伤口情况打卡",
                        "description": "记录红肿、渗液和疼痛变化。",
                        "category": "OBSERVATION",
                        "dueAfterDays": 1,
                    },
                    {
                        "title": "复诊预约确认",
                        "description": "确认术后第 7 天复诊。",
                        "category": "APPOINTMENT",
                        "dueAfterDays": 7,
                    },
                ],
                "observations": [{"type": "WOUND", "unit": None, "frequency": "DAILY"}],
                "medications": [
                    {
                        "drugName": "示例康复用药",
                        "approvalNumber": "国药准字H20260002",
                        "doseText": "按医嘱",
                        "frequencyText": "每日两次",
                    }
                ],
                "alertRules": [
                    {"type": "OBSERVATION_THRESHOLD", "severity": "HIGH"}
                ],
            },
            created_by=doctor_user.id,
        )
        db.add_all([hypertension, recovery])
        await db.flush()

        now = datetime.now(UTC)
        plan = TreatmentPlan(
            id="plan-main",
            template_id=hypertension.id,
            patient_id=patient.id,
            doctor_id=doctor_user.id,
            organization_id=hospital_a.id,
            title="陈安的高血压协同管理计划",
            status="ACTIVE",
            version=1,
            start_date=date.today() - timedelta(days=5),
            content=hypertension.content,
        )
        db.add(plan)
        db.add(
            PatientConsent(
                plan_id=plan.id,
                patient_id=patient.id,
                status="ACTIVE",
            )
        )
        main_tasks = [
            CareTask(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=hospital_a.id,
                title="每日晨间血压记录",
                description="记录收缩压和舒张压。",
                category="OBSERVATION",
                due_at=now + timedelta(hours=3),
                status="PENDING",
            ),
            CareTask(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=hospital_a.id,
                title="完成用药核对",
                description="核对药盒与计划，不自行调整剂量。",
                category="SELF_CARE",
                due_at=now - timedelta(hours=6),
                status="PENDING",
            ),
            CareTask(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=hospital_a.id,
                title="复诊预约确认",
                description="确认下一次门诊时间。",
                category="APPOINTMENT",
                due_at=now + timedelta(days=2),
                status="COMPLETED",
                completed_at=now - timedelta(days=1),
                completed_by=patient_user.id,
            ),
        ]
        db.add_all(main_tasks)
        main_medication = MedicationSchedule(
            plan_id=plan.id,
            patient_id=patient.id,
            organization_id=hospital_a.id,
            drug_name="示例降压片",
            approval_number="国药准字H20260001",
            dose_text="1 片",
            frequency_text="每日一次",
            start_date=date.today() - timedelta(days=5),
        )
        db.add(main_medication)
        await db.flush()
        db.add(
            MedicationLog(
                schedule_id=main_medication.id,
                patient_id=patient.id,
                status="TAKEN",
                reported_by=patient_user.id,
            )
        )
        db.add(
            Observation(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=hospital_a.id,
                type="BLOOD_PRESSURE",
                value_numeric=138,
                unit="mmHg",
                measured_at=now - timedelta(hours=2),
                submitted_by=patient_user.id,
            )
        )
        db.add(
            Alert(
                plan_id=plan.id,
                patient_id=patient.id,
                organization_id=hospital_a.id,
                type="TASK_OVERDUE",
                severity="MEDIUM",
                title="用药核对任务已逾期",
                detail="请确认患者是否完成核对，不自动调整治疗方案。",
                status="OPEN",
            )
        )

        official_drugs = OfficialDataset(
            id="dataset-nmpa",
            source_code="NMPA",
            title="国家药品监督管理局公开药品目录快照（演示子集）",
            version="demo-2026-10-22",
            source_url="https://www.nmpa.gov.cn/",
            published_at=date(2026, 10, 1),
            effective_at=date(2026, 10, 1),
            checksum="demo-nmpa-20261022-a1b2c3d4",
            reviewer="演示数据审核员",
            status="VERIFIED",
            content={
                "records": [
                    {
                        "approvalNumber": "国药准字H20260001",
                        "name": "示例降压片",
                        "manufacturer": "华康示范药业有限公司（虚构）",
                    }
                ]
            },
        )
        official_institutions = OfficialDataset(
            id="dataset-nhc",
            source_code="NHC",
            title="国家卫生健康委医疗机构公开信息快照（演示子集）",
            version="demo-2026-10-22",
            source_url="https://www.nhc.gov.cn/",
            published_at=date(2026, 10, 1),
            effective_at=date(2026, 10, 1),
            checksum="demo-nhc-20261022-e5f6a7b8",
            reviewer="演示数据审核员",
            status="VERIFIED",
            content={
                "records": [
                    {
                        "institutionName": "海州市第一人民医院",
                        "regionCode": "310000",
                    }
                ]
            },
        )
        official_insurance = OfficialDataset(
            id="dataset-nhsa",
            source_code="NHSA",
            title="国家医疗保障局医保药品目录快照（演示子集）",
            version="demo-2026-10-22",
            source_url="https://www.nhsa.gov.cn/",
            published_at=date(2026, 10, 1),
            effective_at=date(2026, 10, 1),
            checksum="demo-nhsa-20261022-c9d0e1f2",
            reviewer="演示数据审核员",
            status="VERIFIED",
            content={
                "records": [
                    {
                        "drugName": "示例降压片",
                        "insuranceLabel": "演示信息，不代表实际报销",
                    }
                ]
            },
        )
        official_statistics = OfficialDataset(
            id="dataset-nbs",
            source_code="NBS",
            title="国家统计局区域人口基线（演示子集）",
            version="demo-2026",
            source_url="https://www.stats.gov.cn/",
            published_at=date(2026, 1, 1),
            effective_at=date(2026, 1, 1),
            checksum="demo-nbs-2026-33445566",
            reviewer="演示数据审核员",
            status="VERIFIED",
            content={"regionCode": "310000", "populationBaseline": 1000000},
        )
        db.add_all(
            [
                official_drugs,
                official_institutions,
                official_insurance,
                official_statistics,
            ]
        )
        product = DrugProduct(
            id="product-demo-1",
            organization_id=pharma.id,
            name="示例降压片",
            approval_number="国药准字H20260001",
            manufacturer="华康示范药业有限公司（虚构）",
            status="ACTIVE",
            verification_status="VERIFIED",
            source_dataset_id=official_drugs.id,
        )
        db.add(product)
        await db.flush()
        db.add(
            SupplyCapacityReport(
                organization_id=pharma.id,
                product_id=product.id,
                region_code="310000",
                period=date.today().strftime("%Y-%m"),
                capacity_units=120000,
                submitted_by=pharma_user.id,
            )
        )
        db.add_all(
            [
                ReviewCase(
                    organization_id=hospital_c.id,
                    type="ORGANIZATION_VERIFICATION",
                    subject="社区医疗中心机构信息待复核",
                    status="PENDING",
                ),
                ReviewCase(
                    organization_id=hospital_a.id,
                    type="PROFILE_UPDATE",
                    subject="医院协同科室信息变更",
                    status="PENDING",
                ),
            ]
        )

        patient_names = [
            "赵晨",
            "钱宁",
            "孙悦",
            "李安",
            "周和",
            "吴桐",
            "郑欣",
            "王林",
            "冯洁",
            "褚然",
            "卫清",
            "蒋禾",
        ]
        org_doctor_pairs = [
            (hospital_a, doctor_user),
            (hospital_b, doctor_b),
            (hospital_c, doctor_c),
        ]
        for index in range(60):
            organization, doctor = org_doctor_pairs[index % len(org_doctor_pairs)]
            synthetic_user = User(
                username=f"demo_patient_{index:02d}",
                password_hash=password_hash,
                display_name=f"{patient_names[index % len(patient_names)]}{index + 1:02d}",
                role="PATIENT",
                seeded_demo=True,
            )
            db.add(synthetic_user)
            await db.flush()
            profile = PatientProfile(
                user_id=synthetic_user.id,
                display_name=synthetic_user.display_name,
                record_number=f"DEMO-2026-{index + 2:04d}",
                region_code="310000",
            )
            db.add(profile)
            await db.flush()
            synthetic_plan = TreatmentPlan(
                template_id=recovery.id if index % 2 else hypertension.id,
                patient_id=profile.id,
                doctor_id=doctor.id,
                organization_id=organization.id,
                title=f"{profile.display_name}的治疗协同计划",
                status="ACTIVE",
                start_date=date.today() - timedelta(days=index % 20),
                content=hypertension.content if index % 2 == 0 else recovery.content,
            )
            db.add(synthetic_plan)
            await db.flush()
            db.add(
                CareTask(
                    plan_id=synthetic_plan.id,
                    patient_id=profile.id,
                    organization_id=organization.id,
                    title="月度随访打卡",
                    description="演示合成任务。",
                    category="SELF_CARE",
                    due_at=now + timedelta(days=3 + index % 7),
                    status="COMPLETED" if index % 4 == 0 else "PENDING",
                )
            )
            db.add(
                MedicationSchedule(
                    plan_id=synthetic_plan.id,
                    patient_id=profile.id,
                    organization_id=organization.id,
                    drug_name="示例降压片",
                    approval_number="国药准字H20260001",
                    dose_text="1 片",
                    frequency_text="每日一次",
                    start_date=date.today() - timedelta(days=index % 20),
                )
            )

        await db.commit()


if __name__ == "__main__":
    import asyncio

    from carepath.db import init_db

    async def main() -> None:
        await init_db()
        await seed_database()

    asyncio.run(main())
