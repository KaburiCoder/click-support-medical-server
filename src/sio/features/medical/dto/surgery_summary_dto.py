"""수술/수술 전후 경과 요약 DTO - 급성기 진료 의사 의사결정 지원"""

from typing import Literal, Optional

from pydantic import Field

from src.common import CamelModel


class SurgeryRiskFlag(CamelModel):
  """수술 관련 위험 신호/주의사항"""

  category: Literal[
      "airway",
      "cardiac",
      "pulmonary",
      "bleeding",
      "infection",
      "thromboembolism",
      "medication",
      "renal",
      "glycemic",
      "neurologic",
      "other",
  ] = Field(..., description="위험 카테고리")
  severity: Literal["low", "moderate", "high", "critical"] = Field(
      ..., description="위험도")
  message: str = Field(..., description="핵심 내용")
  recommended_action: Optional[str] = Field(None, description="권장 조치")


class SurgeryTimelineItem(CamelModel):
  """수술 전후 타임라인"""

  timestamp: str = Field(..., description="일시 (가능하면 yyyy-MM-dd HH:mm:ss)")
  event_type: Literal[
      "preop_assessment",
      "procedure_planned",
      "procedure_performed",
      "anesthesia",
      "postop_course",
      "complication",
      "follow_up",
      "other",
  ] = Field(..., description="이벤트 유형")
  summary: str = Field(..., description="이벤트 요약")
  source: Optional[str] = Field(None, description="근거/출처 (예: 경과기록, 진단기록)")

  course_trend: Literal["improving", "stable", "worsening", "unknown"] = Field(
      "unknown",
      description="해당 이벤트 전후 경과 추세(호전/안정/악화/불명). 데이터 부족 시 unknown"
  )
  course_trend_reason: Optional[str] = Field(
      None,
      description="경과 추세 판단 근거(짧게). 불명확하면 생략"
  )


class SurgeryCase(CamelModel):
  """단일 수술 케이스(계획/시행 포함)"""

  procedure_name: str = Field(..., description="수술명(가능하면 표준화)")
  site_or_side: Optional[str] = Field(None, description="부위/좌우 (예: 우측 어깨)")
  status: Literal["planned", "performed", "unknown"] = Field(
      ..., description="수술 상태")
  anesthesia: Optional[str] = Field(None, description="마취 종류")
  indication: Optional[str] = Field(None, description="수술 적응증/주요 문제")
  date_estimate: Optional[str] = Field(
      None, description="수술 예정/시행일 추정 (yyyy-MM-dd 또는 yyyy-MM-dd HH:mm:ss)"
  )
  periop_summary: Optional[str] = Field(None, description="술전/술후 핵심 요약")
  pending_questions: list[str] = Field(
      default_factory=list, description="현재 데이터로 남는 확인 질문(최대 5개)", max_length=5
  )


class SurgerySummaryResult(CamelModel):
  """수술 관련 요약 결과"""

  has_surgery_related_content: bool = Field(
      ..., description="제공된 데이터에서 수술/술전/술후 관련 기록 존재 여부")
  one_liner: str = Field(
      ..., description="수술 관점 한 줄 요약 (30자 내외)"
  )
  overview: str = Field(
      ..., description="급성기 진료 의사용 수술 관련 핵심 요약 (2-6문장)"
  )

  cases: list[SurgeryCase] = Field(
      default_factory=list, description="수술 케이스 목록 (계획/시행 포함)"
  )
  timeline: list[SurgeryTimelineItem] = Field(
      default_factory=list, description="수술 전후 타임라인(시간순)"
  )

  key_risks: list[SurgeryRiskFlag] = Field(
      default_factory=list, description="수술 관련 위험 신호/주의사항(우선순위순)"
  )

  immediate_actions: list[str] = Field(
      default_factory=list,
      description="지금 당장 확인/오더/협진 등 즉시 조치(최대 7개)",
      max_length=7,
  )
  periop_medication_notes: list[str] = Field(
      default_factory=list,
      description="약물 관련 술전/술후 주의점(중단/재개/상호작용/금식 등)",
      max_length=7,
  )

  confidence: Literal["high", "moderate", "low"] = Field(
      ..., description="수술 요약 신뢰도 (입력 데이터 충실도 기반)"
  )
