from pydantic import Field
from typing import Optional, Literal

from src.common import CamelModel


class SOAP(CamelModel):
  subjective: Optional[str] = Field(None, description="환자의 주관적 증상 및 호소")
  objective: Optional[str] = Field(None, description="의사의 객관적 관찰 및 검사 결과")
  assessment: Optional[str] = Field(None, description="의사의 평가 및 판단")
  plan: Optional[str] = Field(None, description="치료 및 추후 계획")


class ProgressNoteResult(CamelModel):
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


class VsNsSummaryResult(CamelModel):
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


class VsSummaryDetail(CamelModel):
  vital_sign: str = Field(..., description="Vital Sign 항목명")
  recent_value: str = Field(..., description="최근 측정값")
  trend: str = Field(..., description="최근 변화 추이")
  trend_level: Literal['stable', 'increasing', 'decreasing',
                       'unknown'] = Field(..., description="추이 수준")
  remark: str | None = Field(None, description="특이사항 (예: 최고치 기록, 저혈압 주의)")


class NsCarePlan(CamelModel):
  ns_category: str = Field(...,
                           description="간호 기록 구분 타이틀(예: 정신건강, 신체건강, 수명관리 등)")
  care_plan: str = Field(..., description="주의사항 및 간호계획 내용")
  priority: Literal["high", "medium", "low"] = Field(
      "medium", description="우선순위")


class ClinicalPrediction(CamelModel):
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


class PrescriptionAnalysisDetail(CamelModel):
  category: str = Field(...,
                        description="분석 항목 (예: 약물 부담 지수, 다약제 복용, PRN 패턴 등)")
  finding: str = Field(..., description="해당 항목의 분석 결과")
  severity: Literal["low", "moderate", "high", "critical"] = Field(
      ..., description="위험도 수준")
  recommendation: str = Field(..., description="의료진 권고사항")


class MajorMedicationDetail(CamelModel):
  medication_name: str = Field(..., description="약품명")
  dose: float = Field(..., description="1회 투약량(1일 기준)")
  frequency: int = Field(..., description="1일 투약 횟수")
  total_days: int = Field(..., description="총 투약일수")
  note: str = Field(..., description="참고사항 (용법, 특이사항 등)")


class MajorDiagnosisDetail(CamelModel):
  diagnosis_name: str = Field(..., description="진단명")
  icd_code: str = Field(..., description="ICD 코드")
  start_date: str = Field(..., description="개시일자 (YYYY-MM-DD)")


class DrugInteractionAlert(CamelModel):
  drugs: list[str] = Field(..., description="상호작용 약물명 목록")
  interaction_type: str = Field(..., description="상호작용 종류 (예: 상승작용, 길항작용)")
  clinical_impact: str = Field(..., description="임상적 영향")
  severity: Literal["minor", "moderate", "major", "critical"] = Field(
      ..., description="상호작용 심각도")


class PrescriptionSummaryResult(CamelModel):
  major_medications: list[MajorMedicationDetail] = Field(
      ..., description="주요 투여약물 상세 목록")
  major_diagnoses: list[MajorDiagnosisDetail] = Field(
      ..., description="주요 상병 상세 목록")

  medication_burden_index: float = Field(
      ..., description="약물 부담 지수 (0-100, 높을수록 높은 부담)", ge=0, le=100)
  polypharmacy_analysis: str = Field(
      ..., description="다약제 복용 분석 (투약약물 수, 투약일수 등)")
  prn_pattern_analysis: str = Field(
      ..., description="PRN(필요시) 약물 사용 패턴 분석")

  drug_interaction_alerts: list[DrugInteractionAlert] = Field(
      ..., description="중대한 약물 상호작용 알림 목록")

  prescribing_appropriateness: dict[str, str] = Field(
      ..., description="주요 상병별 처방 적합도 평가 (키: 상병명, 값: 평가내용)")

  hidden_risk_signals: list[str] = Field(
      ..., description="숨은 동반질환 및 합병증 위험 신호 목록")

  analysis_details: list[PrescriptionAnalysisDetail] = Field(
      ..., description="상세 분석 항목별 결과")

  overall_assessment: str = Field(
      ..., description="처방 전체 임상 평가 및 종합 의견")

  priority_recommendations: list[str] = Field(
      ..., description="우선순위별 의료진 조치 권고사항 (최대 5개)")

# =-=-==-=-= 검사 =-=-==-=-=
class LabGroup(CamelModel):
  date: str = Field(..., description="검사 일자(yyyy-MM-dd)")
  group_details: list["LabGroupDetail"] = Field(
      ..., description="검사 그룹별 상세 항목들")

class LabGroupDetail(CamelModel):
  test_group_name: str = Field(..., description="검사 그룹명(예: 일반혈액검사, 간기능검사 등)")
  labs: list["LabDetail"] = Field(
      ..., description="그룹에 속한 주요 검사 항목들")

class LabDetail(CamelModel):
  test_name: str = Field(..., description="검사명")
  sub_test_name: str = Field(..., description="세부 검사명")
  result_value: str = Field(..., description="검사 결과 값")
  unit: str = Field(..., description="단위")
  normal_range: str = Field(..., description="정상 범위")
  status: Literal["normal", "up", "down", "critical_up", "critical_down"] = Field(
      ..., description="검사 결과 상태"
  )
  ai_comment: str = Field(..., description="AI 권장 소견")


class LabAbnormalityAlert(CamelModel):
  """검사 결과 중 이상 항목 알림"""
  test_name: str = Field(..., description="검사명")
  result_value: str = Field(..., description="검사 결과값")
  normal_range: str = Field(..., description="정상 범위")
  deviation_severity: Literal["mild", "moderate", "severe", "critical"] = Field(
      ..., description="정상치로부터 이탈도 (경도/중등도/심각/긴급)"
  )
  clinical_significance: str = Field(
      ..., description="임상적 의미 (예: 간기능 저하 우려, 빈혈 있음)"
  )
  priority: Literal["high", "medium", "low"] = Field(
      ..., description="임상적 우선순위"
  )


class LabTrendAnalysis(CamelModel):
  """검사 항목별 시계열 추세 분석"""
  test_name: str = Field(..., description="검사명")
  recent_value: str = Field(..., description="최근 검사값")
  previous_value: Optional[str] = Field(None, description="이전 검사값")
  trend_direction: Literal["improving", "stable", "worsening", "unknown"] = Field(
      ..., description="추세 방향"
  )
  trend_description: str = Field(..., description="추세 설명 (예: 지속적 상승, 안정화 추세)")
  comparison_with_normal: str = Field(
      ..., description="정상값 대비 비교 (예: 정상 상한선의 150%)"
  )


class LabClinicalImplication(CamelModel):
  """검사 결과의 임상적 해석 및 권고"""
  category: str = Field(..., description="검사 항목 분류 (예: 간기능, 신장기능, 혈당대사)")
  summary: str = Field(..., description="해당 카테고리 검사 결과 요약")
  key_findings: list[str] = Field(
      ..., description="주요 소견 목록 (최대 3-4개)",
      max_length=4
  )
  clinical_assessment: str = Field(
      ..., description="임상적 평가 및 해석"
  )
  recommended_actions: list[str] = Field(
      ..., description="권장 조치사항 (예: 재검, 투약 조절, 전문과 협진)"
  )
  urgency: Literal["routine", "soon", "urgent"] = Field(
      ..., description="대응 긴급도"
  )


class LabSummaryResult(CamelModel):
  major_labs: list[LabGroup] = Field(
      ..., description="주요 검사 그룹 목록")
  
  # AI 분석 결과 - 이상 항목 강조
  abnormality_alerts: list[LabAbnormalityAlert] = Field(
      default_factory=list,
      description="이상 검사 항목 알림 (우선순위 내림차순)"
  )
  
  # AI 분석 결과 - 추세 분석
  trend_analyses: list[LabTrendAnalysis] = Field(
      default_factory=list,
      description="주요 검사 항목 시계열 추세 분석"
  )
  
  # AI 분석 결과 - 카테고리별 임상 해석
  clinical_implications: list[LabClinicalImplication] = Field(
      default_factory=list,
      description="검사 카테고리별 임상적 해석 및 권고사항"
  )
  
  # AI 분석 결과 - 종합 의견
  overall_assessment: str = Field(
      ..., description="전체 검사 결과 종합 의견 및 임상 판단"
  )
  
  # AI 분석 결과 - 최우선 권고
  priority_recommendation: str = Field(
      ..., description="의료진에게 전달할 가장 중요한 한 줄 조치 권고"
  )
  
  # AI 분석 결과 - 위험도 평가
  lab_risk_level: Literal["normal", "caution", "warning", "critical"] = Field(
      ..., description="검사 결과 기반 종합 위험도"
  )
  
  # 최근 검사 정보
  latest_test_date: str = Field(..., description="최근 검사 일자 (yyyy-MM-dd)")
  test_count: int = Field(..., description="조회 기간 내 총 검사 횟수")
  

class PatientSummaryResponse(CamelModel):
  progress_notes_summary: ProgressNoteResult=Field(
      ..., description="경과기록 요약 정보")
  vs_ns_summary: VsNsSummaryResult=Field(
      ..., description="활력징후 및 간호기록 요약 정보")
  prescription_summary: PrescriptionSummaryResult=Field(
      ..., description="처방, 상병 요약 정보")
  lab_summary: LabSummaryResult=Field(
      ..., description="검사 결과 요약 정보")
