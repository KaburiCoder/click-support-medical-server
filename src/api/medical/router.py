from fastapi import APIRouter

from src.api.medical.deps import MedicalServiceDep
from src.api.medical.dto import GetMedicalInfoRequestDto

router = APIRouter(prefix="/medical", tags=["medical"])


@router.post("/info")
async def get_medical_info(
    dto: GetMedicalInfoRequestDto,
    service: MedicalServiceDep
):
  """
  의료 정보 조회 엔드포인트

  Args:
      dto: 의료 정보 조회 요청 DTO
      service: MedicalService (의존성 주입)

  Returns:
      의료 정보 응답
  """
  return await service.get_medical_info(dto)
