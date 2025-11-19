from typing import TypedDict

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.func import END, START
from langgraph.graph import StateGraph

from src.api.medical.dto.progress_note_dto import ProgressNoteResult
from src.api.medical.dto.vs_ns_dto import VsNsSummaryResult
from src.constants import llm_models

from src.utils.format_util import hm_to_time, ymd_to_date

from src.sio.features.medical.dto import ProgressNote, VitalSign, NursingRecord
from src.sio.features.medical.models import NsModels, VsModel, VsModels


class MedicalGraphState(TypedDict, total=False):
  data: 'Data'
  progress_notes_summary: ProgressNoteResult
  vs_ns_summary: VsNsSummaryResult


class Data(TypedDict, total=False):
  progressNotes: list[ProgressNote]
  vitalSigns: list[VitalSign]
  nursingRecords: list[NursingRecord]


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

# ! === Define the workflow structure === #
builder.add_node('create_progressnote_summary', create_progressnote_summary)
builder.add_node('create_ns_vs_summary', create_ns_vs_summary)

builder.add_edge(START, 'create_progressnote_summary')
builder.add_edge(START, 'create_ns_vs_summary')

builder.add_edge('create_progressnote_summary', END)
builder.add_edge('create_ns_vs_summary', END)
# ! === Add nodes to the workflow === #
workflow = builder.compile()
