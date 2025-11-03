from sqlalchemy.ext.asyncio import AsyncSession
from src.api.medical.dto import GetMedicalInfoRequestDto


class MedicalService:
  """의료 정보 관련 비즈니스 로직을 담당하는 서비스"""

  def __init__(self, session: AsyncSession):
    self.session = session

  async def get_medical_info(self, dto: GetMedicalInfoRequestDto) -> dict:
    """
    의료 정보 조회

    Args:
        dto: 의료 정보 조회 요청 DTO

    Returns:
        의료 정보 응답
    """
    # 비즈니스 로직 구현 예시
    # self.session을 사용하여 데이터베이스 쿼리 수행

    return {
        "message": "의료 정보 조회 성공",
        "name": dto.name,
        "email": dto.email,
        "role": dto.role,
    }
