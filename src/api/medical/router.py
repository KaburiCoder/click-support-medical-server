from fastapi import APIRouter
from src.api.medical.dto.all_dto import AllResult
from src.api.medical.dto.base_dto import ChartTermRequestDto
from src.api.medical.dto.progress_note_dto import ProgressNoteResult, SummarizeProgressNoteRequestDto
from src.api.medical.graphs import medical_graph
from src.api.medical.service import MedicalServiceDep

router = APIRouter(prefix="/medical", tags=["medical"])


@router.post("/progress-note/summarize", response_model=ProgressNoteResult)
async def summarize_progress_note(
    dto: SummarizeProgressNoteRequestDto,
    service: MedicalServiceDep
):
  """
  경과기록 요약
  """
  return await service.summarize_progress_note(dto)


@router.post("/vs")
async def vs(
    dto: ChartTermRequestDto,
    service: MedicalServiceDep
):
  return await service.vs_summary(dto)


@router.post("/patient/summary", response_model=AllResult)
async def all_summary(
    dto: ChartTermRequestDto,
    service: MedicalServiceDep
):
  result = await medical_graph.workflow.ainvoke({
      'input': {
          'chart': dto.chart,
          'symd': dto.symd,
          'eymd': dto.eymd
      },
      'session': service.session
  })

  return AllResult(
      progress_notes_summary=result['progress_notes_summary'],
      vs_ns_summary=result['vs_ns_summary']
  )
