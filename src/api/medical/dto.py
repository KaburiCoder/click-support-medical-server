from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class GetMedicalInfoRequestDto(BaseModel):
  name: str = Field(..., min_length=2, max_length=50, description="실명")
  email: EmailStr = Field(..., description="이메일 주소 (예: hong@example.com)")
  role: Literal["patient", "doctor", "admin"] = Field(..., description="역할")
