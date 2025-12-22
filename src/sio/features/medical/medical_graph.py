import pandas as pd

from typing import Awaitable, Callable, TypedDict

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.func import END, START
from langgraph.graph import StateGraph

from src.constants import llm_models

from src.sio.features.medical.dto.medical_request import DiagnosisRecord, SummarizePatientRequest
from src.utils.format_util import hm_to_time, ymd_to_date

from src.sio.features.medical.dto import (
    Loading, 
    ProgressNoteResult, 
    VsNsSummaryResult, 
    PrescriptionSummaryResult, 
    LabSummaryResult, 
    RadiologyReport,
    RadiologyAnalysisSummary,
    ClinicalSummaryResult,
)
from src.sio.features.medical.models import NsModels, VsModel, VsModels


class MedicalGraphState(TypedDict, total=False):
  send_loading: Callable[[Loading], Awaitable[None]]
  data: 'Data'
  progress_notes_summary: ProgressNoteResult
  vs_ns_summary: VsNsSummaryResult
  prescription_summary: PrescriptionSummaryResult
  lab_summary: LabSummaryResult
  radiology_summary: RadiologyAnalysisSummary
  clinical_summary: ClinicalSummaryResult


class Data(SummarizePatientRequest, total=False):
  pass


builder = StateGraph[MedicalGraphState](MedicalGraphState)


async def create_progressnote_summary(state: MedicalGraphState) -> MedicalGraphState:
  progressNotes = state.get('data', {}).get('progressNotes', [])
  if not progressNotes:
    return {}

  histories = [
      f"**일시**: {ymd_to_date(r['ymd'])} {hm_to_time(r['time'])}\n**경과기록**: {r['progress']}"
      for r in progressNotes
  ]
  agent = create_agent(
      model=llm_models.gemini_flash_lite,
      response_format=ProgressNoteResult,
      system_prompt="당신은 의사입니다. 환자의 경과기록을 가지고 필요한 정보를 입력합니다.")

  progressnote_history_text = "\n\n---\n".join(histories)
  response = await agent.ainvoke({
      "messages": [HumanMessage(content=progressnote_history_text)]
  })

  result: ProgressNoteResult = response['structured_response']

  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="progress_notes"))

  return {"progress_notes_summary": result}


async def create_ns_vs_summary(state: MedicalGraphState) -> MedicalGraphState:
  # ? === vs ===
  vss = state.get('data', {}).get('vitalSigns', [])
  recent_vs = VsModel()
  recent_vs.add_recently_from_vss(vss)

  vs_list = VsModels()
  vs_list.add_recently_from_vss(vss)
  vs_list_md = vs_list.get_markdown_table()

  # ? === ns ===
  nss = state.get('data', {}).get('nursingRecords', [])
  ns_list = NsModels()
  ns_list.add_from_nss(nss)
  ns_list_md = ns_list.get_markdown_table()

  if not vss and not nss:
    return {}

  agent = create_agent(
      model=llm_models.gemini_flash,
      response_format=VsNsSummaryResult,
      system_prompt="""당신은 의사입니다.
환자의 활력징후와 간호기록을 다음 내용을 작성합니다.
- 바이탈 사인 종합 요약 정보
- 간호기록 종합 요약 정보
- 주의사항
- 의료진 임상 의견
- 전체 임상 평가
- 주요 소견

활력징후와 간호기록은 각각 마크다운 표 형식으로 제공됩니다.""")

  response = await agent.ainvoke({
      "messages": [HumanMessage(content=f"""# 활력징후 기록
{vs_list_md}

---
# 간호기록
{ns_list_md}""")]
  })

  result: VsNsSummaryResult = response['structured_response']

  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="ns_vs"))

  return {"vs_ns_summary": result}


async def create_prescription_summary(state: MedicalGraphState) -> MedicalGraphState:
  medications = state.get('data', {}).get('medications', [])
  diagnosis_records = state.get('data', {}).get('diagnosisRecords', [])
  patient_info = state.get('data', {}).get('patientInfo', {})

  if not medications and not diagnosis_records and not patient_info:
    return {}

  # 환자 성별 나이
  patient_info_text = f"""
- 이름: {patient_info.get('name', '')}
- 성별: {patient_info.get('sex', '')}
- 나이: {patient_info.get('age', '')}
  """.strip()

  # 약물 정보를 마크다운 포맷으로 변환
  medication_details = []
  for med in medications:
    med_info = f"""### {med['medicationName']}
- **투여 기간**: {med['sYmd']} ~ {med['eYmd']} ({med['totalDays']}일)
- **일회투약량**: {med['dose']}
- **횟수**: {med['frequency']}회/일
- **용법**: {med['administration']}
- **참고사항**: {med['note'] or '없음'}"""
    medication_details.append(med_info)

  medications_text = "\n\n".join(medication_details)

  # 진단 정보를 마크다운 포맷으로 변환
  diagnosis_info = []
  for diag_record in diagnosis_records:
    diagnoses_str = ", ".join(
        [f"{d['diagnosisName']} ({d['icdCode']})" for d in diag_record['diagnoses']])
    diagnosis_info.append(f"**{diag_record['ymd']}**: {diagnoses_str}")

  diagnoses_text = "\n".join(diagnosis_info) if diagnosis_info else "진단 기록 없음"

  system_prompt = """당신은 임상약학 전문가이자 의약학 박사입니다.
환자의 처방 약물 정보와 진단 기록을 분석하여 다음 사항들을 평가합니다:

1. **약물 부담 지수**: 투약 중인 약물의 종류, 용량, 기간, 상호작용 등을 종합적으로 평가하여 0-100점으로 부담도 산출
2. **다약제 복용 분석**: 동시투약 약물의 수, 투약 기간 겹침, 복잡도 분석
3. **PRN 약물 사용 패턴**: 필요시 약물의 사용 빈도와 패턴 분석
4. **중대한 약물 상호작용**: 심각한 부작용 또는 효능 변화 가능성 있는 약물 조합 식별
5. **주요 상병별 처방 적합도**: 각 진단명에 대한 처방약물의 적절성 평가
6. **숨은 동반질환 및 합병증 위험 신호**: 현재 처방 약물에서 암시되는 추가 의학적 상태나 위험 신호
7. **임상 평가**: 전체 처방의 적절성, 안전성, 효과성에 대한 종합 의견

분석은 의료진이 실제로 임상 의사결정에 활용할 수 있도록 구체적이고 실행 가능하게 작성하세요."""

  agent = create_agent(
      model=llm_models.gemini_flash,
      response_format=PrescriptionSummaryResult,
      system_prompt=system_prompt)

  response = await agent.ainvoke({
      "messages": [HumanMessage(content=f"""
# 환자 정보
{patient_info_text}

---
# 투약 약물 정보
{medications_text}

---
# 진단 기록
{diagnoses_text}""".strip())]
  })

  result: PrescriptionSummaryResult = response['structured_response']

  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="prescriptions"))

  return {"prescription_summary": result}


async def create_lab_summary(state: MedicalGraphState) -> MedicalGraphState:
  labs = state.get('data', {}).get('labs', [])
  patient_info = state.get('data', {}).get('patientInfo', {})
  diagnosis_records: list[DiagnosisRecord] = state.get(
      'data', {}).get('diagnosisRecords', [])

  if not labs:
    return {}

  # 환자 기본 정보
  patient_info_text = f"""
- 이름: {patient_info.get('name', '')}
- 성별: {patient_info.get('sex', '')}
- 나이: {patient_info.get('age', '')}
  """.strip()

  # === 진단 정보 ===
  # 진단 기록을 마크다운 테이블로 변환
  diagnosis_rows = []
  for diagnosis in diagnosis_records:
    ymd = diagnosis.get('ymd', '')
    diagnoses = diagnosis.get('diagnoses', [])
    for diag in diagnoses:
      icd_code = diag.get('icdCode', '')
      diagnosis_name = diag.get('diagnosisName', '')
      diagnosis_rows.append({'일자': ymd, 'ICD 코드': icd_code, '진단명': diagnosis_name})

  if diagnosis_rows:
    df_diag = pd.DataFrame(diagnosis_rows)
    diagnoses_text = df_diag.to_markdown(index=False)
  else:
    diagnoses_text = "진단 기록 없음"
 
  # === 검사 목록 ===
  latest_test_date = max(lab['ymd'] for lab in labs)

  # 검사 목록 Markdown으로 변환
  df = pd.DataFrame([lab for lab in labs])
  df = df.rename(columns={
      "ymd": "검사일자(yyyyMMdd)"})
  labs_markdown = df.to_markdown(index=False)

  system_prompt = """당신은 임상병리사이자 의료 데이터 분석 전문가입니다.
환자의 검사 결과를 분석하여 다음 사항들을 평가합니다:

1. **이상 항목 알림**: 정상범위를 벗어난 검사 항목들을 심각도와 임상적 의미와 함께 식별
2. **추세 분석**: 시간에 따른 검사값 변화 추이 분석 (개선/안정화/악화)
3. **카테고리별 임상 해석**: 간기능, 신장기능, 혈당대사, 혈액학, 면역학 등 검사 항목을 분류하여 임상적 평가
4. **종합 의견**: 전체 검사 결과에 대한 통합 평가
5. **우선순위 권고**: 가장 중요한 한 줄 조치 사항
6. **위험도 평가**: 검사 결과 기반 종합 위험도 (normal/caution/warning/critical)

분석은 의료진이 실제로 임상 의사결정에 활용할 수 있도록 구체적이고 실행 가능하게 작성하세요.
이상 항목이 없으면 abnormality_alerts는 빈 리스트로, trend_analysis와 clinical_implications도 데이터가 충분하지 않으면 빈 리스트로 설정하세요."""

  agent = create_agent(
      model=llm_models.gemini_flash,
      response_format=LabSummaryResult,
      system_prompt=system_prompt)

  response = await agent.ainvoke({
      "messages": [HumanMessage(content=f"""
# 환자 정보
{patient_info_text}

---
# 최근 진단
{diagnoses_text}

---
# 검사 결과
{labs_markdown}

---
# 요청사항
위 검사 결과를 분석하여 LabSummaryResult 형식으로 다음 정보를 제공하세요:
- abnormality_alerts: 이상 항목들 (우선순위순)
- trend_analysis: 주요 항목의 추세 분석
- clinical_implications: 카테고리별 임상 해석 및 권고
- overall_assessment: 전체 검사 결과 종합 의견
- priority_recommendation: 의료진에게 전달할 가장 중요한 조치 권고
- lab_risk_level: 종합 위험도
- latest_test_date: {latest_test_date}
- test_count: {len(labs)}
- major_labs: 주요 검사 그룹 (일자별 분류)
""".strip())]
  })

  result: LabSummaryResult = response['structured_response']
  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="labs"))

  return {"lab_summary": result}

# ! === 방사선 판독 분석 통합 노드 === #

async def create_radiology_analysis_summary(state: MedicalGraphState) -> MedicalGraphState:
  """방사선 판독 분석 통합 (단일 + 진행 + 통합 분석) - 1번의 AI 호출로 수행"""
  reports: list[RadiologyReport] = state.get('data', {}).get('radiologyReports', [])
  if not reports:
    return {}
  
  patient_info = state.get('data', {}).get('patientInfo', {})
  patient_context = f"{patient_info.get('name', '')} ({patient_info.get('sex', '')}/{patient_info.get('age', '')})"
  
  # === 통합 분석용 프롬프트 준비 ===
  
  # 1. 단일 검사 분석용 데이터
  report: RadiologyReport | None = reports[0] if reports else None
  single_exam_context = ""
  if report:
    single_exam_context = f"""

## [단일 검사 분석 데이터]
검사일시: {report['ymd']} {report['time']}
검사종류: {report['modality']}
검사부위: {report['examType']}
임상소견: {report['findings']}"""
  
  # 2. 진행 추이 분석용 데이터
  progression_context = ""
  if len(reports) >= 2:
    sorted_reports = sorted(reports, key=lambda x: x['ymd'])
    progression_context = "\n## [진행 추이 분석 데이터]\n검사 기록 (시간순):\n"
    for i, r in enumerate(sorted_reports, 1):
      progression_context += f"""
{i}. {r['ymd']} {r['time']}
   - 검사: {r['modality']} ({r['examType']})
   - 소견: {r['findings']}"""
  
  # 3. 통합 임상 분석용 데이터
  # 활력징후 정보
  vss = state.get('data', {}).get('vitalSigns', [])
  vs_list = VsModels()
  vs_list.add_recently_from_vss(vss)
  vital_signs_context = vs_list.get_markdown_table() if vss else "없음"
  
  # 혈액검사 정보
  labs = state.get('data', {}).get('labs', [])
  lab_data_context = "\n".join([f"- {lab['testName']} ({lab['subTestName']}): {lab['resultValue']} {lab['unit']}" for lab in labs[:10]]) if labs else "없음"
  
  # 투약 정보
  medications = state.get('data', {}).get('medications', [])
  medication_context = "\n".join([f"- {med['medicationName']}: {med['dose']} x {med['frequency']}회/일" for med in medications[:10]]) if medications else "없음"
  
  sorted_reports = sorted(reports, key=lambda x: x['ymd'])
  
  # === 통합 프롬프트 구성 ===
  unified_prompt = f"""
# 종합 방사선 판독 분석

## 환자 정보
{patient_context}
{single_exam_context}
{progression_context}

## [통합 임상 분석 데이터]
### 활력징후
{vital_signs_context}

### 혈액 검사
{lab_data_context}

### 투약 정보
{medication_context}

### 모든 방사선 판독 결과 (시간순)
"""
  
  for i, r in enumerate(sorted_reports, 1):
    unified_prompt += f"""
{i}. {r['ymd']} - {r['modality']} ({r['examType']})
   **임상소견**: {r['findings']}
"""
  
  # === 통합 AI 호출 ===
  agent = create_agent(
      model=llm_models.gemini_flash,
      response_format=RadiologyAnalysisSummary,
      system_prompt="""당신은 경험 많은 방사선과 의사입니다.
제시된 방사선 판독 결과를 종합적으로 분석하여 다음 3가지를 동시에 수행합니다:

## 1. [필수] 단일 검사 분석 (summary 필드)
- 주요 소견
- 임상적 의미
- 질병 진행 상황
- 긴급 소견 리스트
- 권장 추적 또는 추가 검사
- 후속 계획
- 임상의학적 의견

## 2. [조건부] 진행 추이 분석 (progression 필드)
- 검사 기록이 2개 이상인 경우만 작성
- 전체 진행 추세 (improvement/stable/progression)
- 주요 변화 사항들 (시간순)
- 질병 진행 타임라인
- 향후 예상 결과
- 임상적 의미
- 권장 후속 조치

## 3. [필수] 통합 임상 분석 (integrated_analysis 필드)
- 방사선 소견과 활력징후의 연관성
- 혈액 검사 결과와의 일치성
- 투약 반응도 평가
- 현재 환자의 질병 상태 종합 평가
- 질병 진행 양상과 치료 반응도
- 종합 진단 평가 및 필요한 조정 사항
- 우선순위별 추적 관찰 계획과 필요한 추가 검사
- 종합 위험도 평가 (low/moderate/high/critical)

## 응답 규칙:
- progression 필드: 검사 기록이 1개이면 null로 반환, 2개 이상이면 작성
- summary와 integrated_analysis: 항상 작성""")
  
  response = await agent.ainvoke({
      "messages": [HumanMessage(content=unified_prompt)]
  })
   
  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="radiology"))
  
  return {"radiology_summary":  response['structured_response']}


# ! === 종합 임상 요약 노드 (최종 병합) === #

async def create_clinical_summary(state: MedicalGraphState) -> MedicalGraphState:
  """모든 분석 결과를 통합하여 진료실용 종합 임상 요약 생성"""
  from datetime import datetime
  
  # 이전 노드들의 결과 수집
  progress_notes = state.get('progress_notes_summary')
  vs_ns = state.get('vs_ns_summary')
  prescription = state.get('prescription_summary')
  lab = state.get('lab_summary')
  radiology = state.get('radiology_summary')
  patient_info = state.get('data', {}).get('patientInfo', {})
  
  # 데이터 완전성 평가
  data_sources = []
  if progress_notes:
    data_sources.append("경과기록")
  if vs_ns:
    data_sources.append("활력징후/간호기록")
  if prescription:
    data_sources.append("처방/투약")
  if lab:
    data_sources.append("검사결과")
  if radiology:
    data_sources.append("영상판독")
  
  data_completeness = "complete" if len(data_sources) >= 4 else "partial" if len(data_sources) >= 2 else "limited"
  
  # 환자 정보 컨텍스트
  patient_context = f"""
# 환자 정보
- 이름: {patient_info.get('name', '미상')}
- 성별: {patient_info.get('sex', '미상')}
- 나이: {patient_info.get('age', '미상')}
- 최근 방문일: {patient_info.get('lastVisitYmd', '미상')}
""".strip()
  
  # 각 분석 결과 요약 컨텍스트 구성
  analysis_context = ""
  
  # 1. 경과기록 요약
  if progress_notes:
    analysis_context += f"""
---
## 경과기록 분석 결과
- **요약**: {progress_notes.summary}
- **주진단**: {', '.join(progress_notes.main_diagnosis) if progress_notes.main_diagnosis else '없음'}
- **주호소**: {progress_notes.chief_complaint or '없음'}
- **SOAP**:
  - Subjective: {progress_notes.soap.subjective or '없음'}
  - Objective: {progress_notes.soap.objective or '없음'}
  - Assessment: {progress_notes.soap.assessment or '없음'}
  - Plan: {progress_notes.soap.plan or '없음'}
- **주의사항**: {progress_notes.precautions or '없음'}
"""
  
  # 2. 활력징후/간호기록 요약
  if vs_ns:
    analysis_context += f"""
---
## 활력징후 및 간호기록 분석 결과
- **VS 점수**: {vs_ns.vs_score}/5
- **VS 요약**: {vs_ns.vs_summary}
- **간호기록 요약**: {vs_ns.ns_summary}
- **전반적 위험도**: {vs_ns.overall_risk_level}
- **핵심 권고**: {vs_ns.key_recommendation}
- **임상 예측**:
"""
    for pred in vs_ns.clinical_predictions[:3]:
      analysis_context += f"  - [{pred.timeframe}] {pred.predicted_risk}: {pred.recommended_action}\n"
  
  # 3. 처방 분석 요약
  if prescription:
    analysis_context += f"""
---
## 처방/투약 분석 결과
- **약물 부담 지수**: {prescription.medication_burden_index}/100
- **다약제 복용 분석**: {prescription.polypharmacy_analysis}
- **PRN 패턴**: {prescription.prn_pattern_analysis}
- **주요 투약약물**: {', '.join([med.medication_name for med in prescription.major_medications[:5]])}
- **주요 상병**: {', '.join([diag.diagnosis_name for diag in prescription.major_diagnoses[:3]])}
- **종합 평가**: {prescription.overall_assessment}
- **숨은 위험 신호**: {', '.join(prescription.hidden_risk_signals[:3]) if prescription.hidden_risk_signals else '없음'}
- **우선 권고**:
"""
    for rec in prescription.priority_recommendations[:3]:
      analysis_context += f"  - {rec}\n"
  
  # 4. 검사 결과 요약
  if lab:
    analysis_context += f"""
---
## 검사 결과 분석
- **검사 위험도**: {lab.lab_risk_level}
- **최근 검사일**: {lab.latest_test_date}
- **검사 횟수**: {lab.test_count}회
- **종합 평가**: {lab.overall_assessment}
- **우선 권고**: {lab.priority_recommendation}
- **이상 항목 알림**:
"""
    for alert in lab.abnormality_alerts[:3]:
      analysis_context += f"  - [{alert.priority}] {alert.test_name}: {alert.result_value} ({alert.clinical_significance})\n"
  
  # 5. 영상 판독 요약
  if radiology and radiology.summary:
    analysis_context += f"""
---
## 영상 판독 분석 결과
- **주요 소견**: {radiology.summary.main_finding}
- **임상적 의미**: {radiology.summary.clinical_significance}
- **진행 분석**: {radiology.summary.progression_analysis}
- **긴급 소견**: {', '.join(radiology.summary.urgent_findings) if radiology.summary.urgent_findings else '없음'}
- **임상 의견**: {radiology.summary.clinical_opinion}
"""
    if radiology.integrated_analysis:
      analysis_context += f"""- **통합 위험도**: {radiology.integrated_analysis.risk_level}
- **통합 임상 의견**: {radiology.integrated_analysis.integrated_clinical_opinion}
"""

  system_prompt = """당신은 대학병원 수석 전문의이자 임상 의사결정 지원 전문가입니다.
여러 임상 데이터 분석 결과를 통합하여 진료실 의료진이 즉시 활용할 수 있는 종합 임상 요약을 작성합니다.

## 핵심 목표
1. **즉각적 의사결정 지원**: 의료진이 환자 접촉 전 1분 내 핵심 파악 가능
2. **우선순위 기반 알림**: 긴급성에 따른 조치 사항 명확화
3. **위험 요소 시각화**: 복합적 위험을 직관적으로 전달
4. **인계 효율화**: SBAR 형식의 명확한 상태 전달

## 작성 원칙
- 모든 분석 결과의 핵심만 추출하여 통합
- 중복 정보 제거, 상충 정보는 더 신뢰할 수 있는 소스 우선
- 불확실한 부분은 명시적으로 표기
- 즉각적 조치 필요 사항 최우선 배치
- 한 줄 요약은 의료진이 복도에서도 파악 가능한 수준

## 응답 형식
ClinicalSummaryResult 스키마를 정확히 따라 작성하세요.

## 중요 지침
- priority_alerts는 urgent > warning > attention > info 순으로 정렬
- key_recommendations는 critical > high > medium > low 순으로 정렬
- one_liner는 30자 이내로 핵심만 (예: "DM 조절 악화, 인슐린 조정 필요")
- 데이터가 없는 영역은 제공된 정보 범위 내에서 합리적 추론, 단 신뢰도 반영
"""

  agent = create_agent(
      model=llm_models.gemini_flash,
      response_format=ClinicalSummaryResult,
      system_prompt=system_prompt)

  response = await agent.ainvoke({
      "messages": [HumanMessage(content=f"""
{patient_context}

# 분석 결과 통합

사용 가능한 데이터 소스: {', '.join(data_sources)}
데이터 완전성: {data_completeness}

{analysis_context}

---
# 요청사항
위 모든 분석 결과를 종합하여 ClinicalSummaryResult 형식의 종합 임상 요약을 생성하세요.

현재 분석 시점: {datetime.now().isoformat()}

진료실 의료진이 환자를 보기 직전 1분 내에 전체 상황을 파악하고 
핵심 조치사항을 인지할 수 있도록 작성해주세요.
""".strip())]
  })
  
  result: ClinicalSummaryResult = response['structured_response']
  
  if 'send_loading' in state:
    await state['send_loading'](Loading(complete_target="clinical_summary"))
  
  return {"clinical_summary": result}


# ! === Define the workflow structure === #
# 병렬 처리 노드
builder.add_node('create_progressnote_summary', create_progressnote_summary)
builder.add_node('create_ns_vs_summary', create_ns_vs_summary)
builder.add_node('create_prescription_summary', create_prescription_summary)
builder.add_node('create_lab_summary', create_lab_summary)
builder.add_node('create_radiology_analysis_summary', create_radiology_analysis_summary)

# 최종 통합 노드
builder.add_node('create_clinical_summary', create_clinical_summary)

# 시작 -> 병렬 처리
builder.add_edge(START, 'create_progressnote_summary')
builder.add_edge(START, 'create_ns_vs_summary')
builder.add_edge(START, 'create_prescription_summary')
builder.add_edge(START, 'create_lab_summary')
builder.add_edge(START, 'create_radiology_analysis_summary')

# 병렬 처리 -> 최종 통합
builder.add_edge('create_progressnote_summary', 'create_clinical_summary')
builder.add_edge('create_ns_vs_summary', 'create_clinical_summary')
builder.add_edge('create_prescription_summary', 'create_clinical_summary')
builder.add_edge('create_lab_summary', 'create_clinical_summary')
builder.add_edge('create_radiology_analysis_summary', 'create_clinical_summary')

# 최종 통합 -> 종료
builder.add_edge('create_clinical_summary', END)

workflow = builder.compile()
