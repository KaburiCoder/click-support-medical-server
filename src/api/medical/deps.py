from typing import Annotated

from fastapi import Depends
from src.api.deps import SessionDep
from src.api.medical.service import MedicalService


def get_medical_service(session: SessionDep) -> MedicalService:
  return MedicalService(session)


MedicalServiceDep = Annotated[MedicalService, Depends(get_medical_service)]
