"""종합 임상 요약 DTO - 진료실 사용자를 위한 최종 통합 분석 결과"""

from typing import Literal, Optional
from pydantic import Field
from src.common import CamelModel


# ===== 환자 상태 개요 =====

class PatientStatusOverview(CamelModel):
    """환자 상태 개요 - 한눈에 파악 가능한 핵심 정보"""
    overall_condition: Literal["stable", "improving", "declining", "critical"] = Field(
        ..., description="환자 전반적 상태")
    acuity_level: Literal["low", "moderate", "high", "critical"] = Field(
        ..., description="환자 중증도")
    admission_risk: Literal["low", "moderate", "high"] = Field(
        ..., description="입원/악화 위험도")
    key_status_summary: str = Field(..., description="환자 상태 핵심 요약 (1-2문장)")


# ===== 우선순위 알림 시스템 =====

class PriorityAlert(CamelModel):
    """우선순위 기반 알림 - 즉각 조치 필요 항목"""
    alert_type: Literal["urgent", "warning", "attention", "info"] = Field(
        ..., description="알림 유형")
    category: Literal["vital_sign", "medication", "lab", "radiology", "clinical"] = Field(
        ..., description="알림 카테고리")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 내용")
    source: str = Field(..., description="데이터 출처 (예: 활력징후, 검사결과)")
    recommended_action: str = Field(..., description="권장 조치")
    time_sensitivity: Optional[str] = Field(None, description="시간 민감도 (예: 즉시, 24시간 내)")


# ===== 진단 및 평가 =====

class DiagnosisSummary(CamelModel):
    """진단 종합 - 현재 및 의심 진단"""
    primary_diagnosis: str = Field(..., description="주진단명")
    icd_code: Optional[str] = Field(None, description="주진단 ICD 코드")
    secondary_diagnoses: list[str] = Field(default_factory=list, description="부진단 목록")
    suspected_conditions: list[str] = Field(default_factory=list, description="추가 의심 상태/합병증")
    disease_stage: Optional[str] = Field(None, description="질병 단계/진행도 (해당 시)")
    prognosis_outlook: str = Field(..., description="예후 전망")


# ===== 치료 계획 요약 =====

class TreatmentPlanItem(CamelModel):
    """개별 치료 계획 항목"""
    category: Literal["medication", "procedure", "monitoring", "consultation", "lifestyle", "follow_up"] = Field(
        ..., description="치료 계획 유형")
    priority: Literal["immediate", "short-term", "long-term"] = Field(
        ..., description="우선순위")
    description: str = Field(..., description="치료 계획 상세")
    rationale: str = Field(..., description="근거/이유")
    expected_outcome: Optional[str] = Field(None, description="예상 결과")


class TreatmentPlanSummary(CamelModel):
    """치료 계획 종합"""
    current_treatment_summary: str = Field(..., description="현재 치료 요약")
    medication_adjustments: list[str] = Field(default_factory=list, description="약물 조정 권고")
    planned_items: list[TreatmentPlanItem] = Field(default_factory=list, description="계획된 치료 항목들")
    follow_up_recommendations: list[str] = Field(default_factory=list, description="추적관찰 권고")


# ===== 위험 평가 대시보드 =====

class RiskIndicator(CamelModel):
    """위험 지표"""
    risk_category: str = Field(..., description="위험 카테고리 (예: 심혈관, 감염, 낙상)")
    risk_level: Literal["low", "moderate", "high", "critical"] = Field(
        ..., description="위험 수준")
    risk_score: Optional[int] = Field(None, description="위험 점수 (0-100)", ge=0, le=100)
    contributing_factors: list[str] = Field(default_factory=list, description="위험 기여 요인")
    mitigation_strategy: str = Field(..., description="위험 완화 전략")


class RiskDashboard(CamelModel):
    """위험 평가 대시보드"""
    overall_risk_level: Literal["low", "moderate", "high", "critical"] = Field(
        ..., description="전반적 위험 수준")
    risk_score: int = Field(..., description="종합 위험 점수 (0-100)", ge=0, le=100)
    risk_indicators: list[RiskIndicator] = Field(default_factory=list, description="개별 위험 지표들")
    time_sensitive_risks: list[str] = Field(default_factory=list, description="시간 민감 위험 요소")


# ===== 임상 트렌드 분석 =====

class TrendAnalysisItem(CamelModel):
    """개별 트렌드 분석 항목"""
    parameter: str = Field(..., description="분석 파라미터 (예: 혈압, 신장기능)")
    trend_direction: Literal["improving", "stable", "declining", "fluctuating"] = Field(
        ..., description="추세 방향")
    recent_change: str = Field(..., description="최근 변화 설명")
    clinical_significance: str = Field(..., description="임상적 의미")
    projection: Optional[str] = Field(None, description="향후 예측")


class ClinicalTrendSummary(CamelModel):
    """임상 트렌드 요약"""
    overall_trajectory: Literal["improving", "stable", "declining", "mixed"] = Field(
        ..., description="전반적 궤적")
    key_trends: list[TrendAnalysisItem] = Field(default_factory=list, description="주요 트렌드 항목들")
    trend_concerns: list[str] = Field(default_factory=list, description="우려되는 트렌드")
    positive_indicators: list[str] = Field(default_factory=list, description="긍정적 지표")


# ===== 핵심 권고사항 =====

class ClinicalRecommendation(CamelModel):
    """임상 권고사항"""
    priority: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="우선순위")
    category: Literal["diagnostic", "therapeutic", "monitoring", "consultation", "patient_education"] = Field(
        ..., description="권고 유형")
    recommendation: str = Field(..., description="권고 내용")
    rationale: str = Field(..., description="근거")
    timeframe: str = Field(..., description="시행 시기 (예: 즉시, 24시간 내, 다음 방문)")
    expected_benefit: str = Field(..., description="예상 효과")


# ===== 의료진 커뮤니케이션 요약 =====

class HandoffSummary(CamelModel):
    """의료진 인계 요약"""
    situation: str = Field(..., description="현재 상황 (SBAR - Situation)")
    background: str = Field(..., description="배경 (SBAR - Background)")
    assessment: str = Field(..., description="평가 (SBAR - Assessment)")
    recommendation: str = Field(..., description="권고 (SBAR - Recommendation)")
    watch_list: list[str] = Field(default_factory=list, description="주의 관찰 사항")
    pending_items: list[str] = Field(default_factory=list, description="미결/대기 항목")


# ===== 최종 통합 임상 요약 =====

class ClinicalSummaryResult(CamelModel):
    """종합 임상 요약 - 진료실 최종 의사결정 지원"""
    
    # 환자 상태 개요
    patient_status: PatientStatusOverview = Field(
        ..., description="환자 상태 개요")
    
    # 우선순위 알림 (즉각 주의 필요 항목)
    priority_alerts: list[PriorityAlert] = Field(
        default_factory=list, description="우선순위 알림 목록")
    
    # 진단 종합
    diagnosis_summary: DiagnosisSummary = Field(
        ..., description="진단 종합")
    
    # 위험 평가 대시보드
    risk_dashboard: RiskDashboard = Field(
        ..., description="위험 평가 대시보드")
    
    # 임상 트렌드
    clinical_trends: ClinicalTrendSummary = Field(
        ..., description="임상 트렌드 분석")
    
    # 치료 계획
    treatment_plan: TreatmentPlanSummary = Field(
        ..., description="치료 계획 요약")
    
    # 핵심 권고사항 (우선순위순)
    key_recommendations: list[ClinicalRecommendation] = Field(
        default_factory=list, description="핵심 권고사항 (우선순위순)")
    
    # 의료진 인계용 요약 (SBAR)
    handoff_summary: HandoffSummary = Field(
        ..., description="의료진 인계 요약")
    
    # 메타 정보
    analysis_timestamp: str = Field(..., description="분석 시점 (ISO 8601)")
    confidence_score: int = Field(..., description="분석 신뢰도 점수 (0-100)", ge=0, le=100)
    data_completeness: Literal["complete", "partial", "limited"] = Field(
        ..., description="데이터 완전성")
    
    # 진료실 즉시 사용 가능한 한 줄 요약
    one_liner: str = Field(
        ..., description="환자 상태 한 줄 요약 (진료실 표시용)")
