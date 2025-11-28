from typing import TypedDict, Literal, Optional
from pydantic import Field
from src.common import CamelModel


class RadiologyReport(TypedDict):
  """방사선 판독 결과"""
  ymd: str                          # 검사일자
  time: str                         # 검사시간
  modality: str                     # 검사 종류 (X-ray, CT, MRI, Ultrasound, PET 등)
  examType: str                     # 검사 부위 (흉부, 복부, 척추 등)
  findings: str                   # 임상 소견 (주요 결론)

# =-=-= Response DTOs (CamelModel) =-=-=


class RadiologySingleFinding(CamelModel):
  """개별 소견 - 응답용"""
  location: str = Field(..., description="검사 위치")
  finding: str = Field(..., description="소견")
  severity: Literal["normal", "mild", "moderate",
                    "severe"] = Field(..., description="심각도")
  description: str = Field(..., description="상세 설명")


class RadiologySummaryResult(CamelModel):
  """방사선 판독 결과 AI 분석 요약"""
  main_finding: str = Field(..., description="주요 소견")
  clinical_significance: str = Field(..., description="임상적 의미")
  progression_analysis: str = Field(..., description="질병 진행 상황 분석 (이전과 비교)")
  urgent_findings: list[str] = Field(
      default_factory=list, description="긴급 소견 리스트")
  recommendations: list[str] = Field(
      default_factory=list, description="권장 추적 또는 추가 검사")
  follow_up_plan: str = Field(..., description="후속 계획")
  clinical_opinion: str = Field(..., description="임상의학적 의견")


class RadiologyProgressionResult(CamelModel):
  """방사선 판독 결과의 질병 진행 분석"""
  overall_trend: Literal["improvement", "stable",
                         "progression"] = Field(..., description="전체 진행 추세")
  key_changes: list[str] = Field(..., description="주요 변화 사항")
  evolution_timeline: str = Field(..., description="시간 경과에 따른 변화 시간표")
  predicted_outcome: str = Field(..., description="예상 결과")
  clinical_implications: str = Field(..., description="임상적 의미")
  recommended_follow_up: list[str] = Field(..., description="권장 후속 조치")


class IntegratedClinicalAnalysisResult(CamelModel):
  """방사선 판독 결과와 다른 임상 데이터의 통합 분석"""
  clinical_correlation_analysis: str = Field(..., description="임상적 상관관계 분석")
  overall_clinical_picture: str = Field(..., description="질병의 전체 그림 평가")
  progression_assessment: str = Field(..., description="진행 추이 및 예후")
  integrated_clinical_opinion: str = Field(..., description="통합 임상 의견")
  management_recommendations: list[str] = Field(..., description="환자 관리 권고사항")
  priority_actions: list[str] = Field(..., description="우선순위별 조치사항")
  risk_level: Literal["low", "moderate", "high",
                      "critical"] = Field(..., description="종합 위험도")

class RadiologyAnalysisSummary(CamelModel):
  """방사선 분석 결과 통합 래퍼"""
  summary: Optional[RadiologySummaryResult] = Field(
      None, description="단일 검사 분석 결과")
  progression: Optional[RadiologyProgressionResult] = Field(
      None, description="질병 진행 분석 결과")
  integrated_analysis: Optional[IntegratedClinicalAnalysisResult] = Field(
      None, description="통합 임상 분석 결과")
