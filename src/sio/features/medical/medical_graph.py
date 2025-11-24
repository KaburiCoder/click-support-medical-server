from typing import TypedDict

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.func import END, START
from langgraph.graph import StateGraph

from src.constants import llm_models

from src.sio.features.medical.dto.medical_request import SummarizePatientRequest
from src.utils.format_util import hm_to_time, ymd_to_date

from src.sio.features.medical.dto import DiagnosisRecord, Medication, PatientInfo, ProgressNote, ProgressNoteResult, VitalSign, NursingRecord, VsNsSummaryResult, PrescriptionSummaryResult, LabSummaryResult, Lab
from src.sio.features.medical.models import NsModels, VsModel, VsModels


class MedicalGraphState(TypedDict, total=False):
  data: 'Data'
  progress_notes_summary: ProgressNoteResult
  vs_ns_summary: VsNsSummaryResult
  prescription_summary: PrescriptionSummaryResult
  lab_summary: LabSummaryResult


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
- **투여 경로**: {med['route']}
- **용량**: 1회 {med['dose']}회, {med['frequency']}회/일
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
  return {"prescription_summary": result}

async def create_lab_summary(state: MedicalGraphState) -> MedicalGraphState:
  labs = state.get('data', {}).get('labs', [])
  patient_info = state.get('data', {}).get('patientInfo', {})
  diagnosis_records = state.get('data', {}).get('diagnosisRecords', [])
  
  if not labs:
    return {}

  # 환자 기본 정보
  patient_info_text = f"""
- 이름: {patient_info.get('name', '')}
- 성별: {patient_info.get('sex', '')}
- 나이: {patient_info.get('age', '')}
  """.strip()

  # 최근 검사 정보 추출
  latest_test_date = labs[0]['ymd'] if labs else ''
  
  # 진단 정보
  recent_diagnoses = []
  if diagnosis_records:
    recent_diagnoses = diagnosis_records[-1].get('diagnoses', [])
  diagnoses_text = ", ".join(
      [f"{d['diagnosisName']} ({d['icdCode']})" for d in recent_diagnoses]
  ) if recent_diagnoses else "진단 기록 없음"

  # 검사 정보를 마크다운 테이블 형식으로 변환
  lab_details = []
  for lab in labs:
    lab_detail = f"""| {lab['testName']} | {lab['subTestName']} | {lab['resultValue']} | {lab['unit']} | {lab['normalRange']} | {lab['note'] or '없음'} |"""
    lab_details.append(lab_detail)

  labs_markdown = """| 검사 분류 | 검사 항목 | 결과값 | 단위 | 정상범위 | 비고 |
|----------|---------|--------|------|---------|------|
""" + "\n".join(lab_details)

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
  dump_data = result.model_dump(by_alias=True)
  return {"lab_summary": result}

# ! === Define the workflow structure === #
builder.add_node('create_progressnote_summary', create_progressnote_summary)
builder.add_node('create_ns_vs_summary', create_ns_vs_summary)
builder.add_node('create_prescription_summary', create_prescription_summary)
builder.add_node('create_lab_summary', create_lab_summary)

builder.add_edge(START, 'create_progressnote_summary')
builder.add_edge(START, 'create_ns_vs_summary')
builder.add_edge(START, 'create_prescription_summary')
builder.add_edge(START, 'create_lab_summary')

builder.add_edge('create_progressnote_summary', END)
builder.add_edge('create_ns_vs_summary', END)
builder.add_edge('create_prescription_summary', END)
builder.add_edge('create_lab_summary', END)
workflow = builder.compile()
