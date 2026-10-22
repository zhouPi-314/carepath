"""Repository adapters for core aggregates.

Repositories encapsulate SQLAlchemy queries so application services and
routers do not build queries inline. Each repository takes an AsyncSession
owned by a unit of work.
"""

from carepath.repositories.care_plans import TreatmentPlanRepository
from carepath.repositories.care_tasks import CareTaskRepository
from carepath.repositories.patients import PatientRepository

__all__ = [
    "CareTaskRepository",
    "PatientRepository",
    "TreatmentPlanRepository",
]
