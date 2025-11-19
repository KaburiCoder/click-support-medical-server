from pydantic import Field
from typing import Optional, Literal

from src.common import CarmelModel


class SOAP(CarmelModel):
  subjective: Optional[str] = Field(None, description="환자의 주관적 증상 및 호소")
  objective: Optional[str] = Field(None, description="의사의 객관적 관찰 및 검사 결과")
  assessment: Optional[str] = Field(None, description="의사의 평가 및 판단")
  plan: Optional[str] = Field(None, description="치료 및 추후 계획")


class ProgressNoteResult(CarmelModel):
  summary: str = Field(..., description="경과기록 전체 요약")
  main_diagnosis: list[str] = Field(..., description="주진단명 또는 주요 진단 코드")
  chief_complaint: Optional[str] = Field(None, description="주요 증상 및 호소")
  soap: SOAP = Field(..., description="SOAP 및 주진단 정보")
  precautions: str = Field(
      ..., description="AI가 도출한 주의 사항 없을 시 빈문자열")
  start_date: str = Field(...,
                          description="요약에 사용된 처음 일시(yyyy-MM-dd HH:mm:ss)")
  end_date: str = Field(
      ..., description="요약에 사용된 마지막 일시(yyyy-MM-dd HH:mm:ss)")


class VsNsSummaryResult(CarmelModel):
  vs_score: int = Field(..., description="Vital Sign 종합 점수(1-5점)", ge=1, le=5)
  vs_summary: str = Field(...,
                          description="Vital Sign 종합 요약(Markdown 형식 - `\\n` 줄바꿈 없이)")
  vs_details: list["VsSummaryDetail"] = Field(
      ..., description="Vital Sign 세부 항목별 요약")
  vs_notes: list[str] = Field(..., description="Vital Sign 의사 참고사항 목록")

  ns_summary: str = Field(...,
                          description="간호 기록 종합 요약(Markdown 형식 - `\\n` 줄바꿈 없이)")
  ns_care_plans: list["NsCarePlan"] = Field(...,
                                            description="주요 주의사항 및 간호 계획 목록")
  ns_observation_details: list[str] = Field(
      ...,
      description="간호 관찰 주요 기록 (텍스트 나열, 예: ['혈압: 정상 범위 내 (135/84)', '환자 의식 명확함', ...])",
      max_length=5
  )

  # 여기부터 추가된 예측 분석 항목
  clinical_predictions: list["ClinicalPrediction"] = Field(
      ...,
      description="향후 경과 예측 분석 (의료진 판단 보조용)"
  )
  overall_risk_level: Literal["low", "moderate", "high", "critical"] = Field(
      ...,
      description="현재 시점 종합 위험도 (활력징후 + 간호기록 + 예측 기반)"
  )
  key_recommendation: str = Field(
      ...,
      description="의료진에게 전달할 가장 중요한 한 줄 권고 (예: '정신과 협진 후 약물 증량 검토 요망')"
  )


class VsSummaryDetail(CarmelModel):
  vital_sign: str = Field(..., description="Vital Sign 항목명")
  recent_value: str = Field(..., description="최근 측정값")
  trend: str = Field(..., description="최근 변화 추이")
  trend_level: Literal['stable', 'increasing', 'decreasing',
                       'unknown'] = Field(..., description="추이 수준")
  remark: str | None = Field(None, description="특이사항 (예: 최고치 기록, 저혈압 주의)")


class NsCarePlan(CarmelModel):
  ns_category: str = Field(...,
                           description="간호 기록 구분 타이틀(예: 정신건강, 신체건강, 수명관리 등)")
  care_plan: str = Field(..., description="주의사항 및 간호계획 내용")
  priority: Literal["high", "medium", "low"] = Field(
      "medium", description="우선순위")


class ClinicalPrediction(CarmelModel):
  timeframe: Literal["24-48시간", "3-7일", "1-4주", "장기(1개월 이상)"] = Field(
      ..., description="예측 기간"
  )
  predicted_risk: str = Field(...,
                              description="예측되는 주요 위험 (예: 재발성 망상, 낙상, 감염)")
  confidence: Literal["high", "moderate",
                      "low"] = Field(..., description="예측 신뢰도")
  rationale: str = Field(..., description="예측 근거 요약 (활력징후 추이, 행동 패턴, 과거 이력 등)")
  recommended_action: str = Field(...,
                                  description="권장 선제적 조치 (예: 약물 증량, 1:1 관찰, 외진 예약)")
