"""의료 관련 네임스페이스"""
from typing import get_type_hints
from src.sio.config import sio
from src.sio.base import BaseNamespace
from src.sio.features.medical import medical_graph
from src.sio.features.medical.dto import (
    Loading, 
    PatientSummaryResponse, 
    PrescriptionSummaryResult, 
    ProgressNoteResult, 
    SummarizePatientRequest, 
    VsNsSummaryResult, 
    LabSummaryResult,
)


class MedicalNamespace(BaseNamespace):
  """의료 관련 네임스페이스"""

  namespace = "/medical"

  def register_events(self) -> None:
    """의료 네임스페이스 이벤트 등록"""

    @sio.event(namespace=self.namespace)
    async def connect(sid: str, environ: dict):
      """클라이언트가 /medical 네임스페이스에 연결"""
      print(f"[{self.namespace}] 클라이언트 연결: {sid}")

    @sio.event(namespace=self.namespace)
    async def disconnect(sid: str):
      """클라이언트가 /medical 네임스페이스에서 연결 해제"""
      print(f"[{self.namespace}] 클라이언트 연결 해제: {sid}")

    @sio.event(namespace=self.namespace)
    async def join_room(sid: str, room: str):
      """클라이언트를 특정 룸에 참여시키기"""
      print(f"[{self.namespace}] join_room - sid: {sid}, room: {room}")
      await self.enter_room(sid, room)

      return True

    @sio.event(namespace=self.namespace)
    async def leave_room(sid: str, room: str):
      """클라이언트를 특정 룸에서 나가기"""
      print(f"[{self.namespace}] leave_room - sid: {sid}, room: {room}")
      await self.leave_room(sid, room)

    @sio.event(namespace=self.namespace)
    async def summarize_patient(sid: str, to: str, data: SummarizePatientRequest):
      """환자 요약 정보 요청"""
      print(
          f"[{self.namespace}] summarize_patient - sid: {sid}, patient_id: {to}, data: {data}")

      # 환자 정보 전송
      await self.emit_with_ack("patient_data", data["patientInfo"], to=to)

      # === 로딩 상태 전송 함수 정의 ===
      async def send_loading(loading: Loading) -> None:
        """로딩 상태 전송"""
        await self.emit("loading", loading.to_json(), room=to)

      # 처리 중 상태 전송

      await send_loading(Loading(status="processing"))

      result = await medical_graph.workflow.ainvoke({
          "send_loading": send_loading,
          "data": data
      })
      # room의 모든 클라이언트로부터 응답 수집

      # Pydantic 모델을 dict로 변환 (JSON 직렬화 가능)
      progress_notes_summary: ProgressNoteResult = result['progress_notes_summary']
      vs_ns_summary: VsNsSummaryResult = result["vs_ns_summary"]
      prescription_summary: PrescriptionSummaryResult = result["prescription_summary"]
      lab_summary: LabSummaryResult = result["lab_summary"]

      response = PatientSummaryResponse(
          progress_notes_summary=progress_notes_summary,
          vs_ns_summary=vs_ns_summary,
          prescription_summary=prescription_summary,
          lab_summary=lab_summary,
          radiology_summary=result.get('radiology_summary')
      )
      responses = await self.emit_with_ack(
          "summarize_patient",
          response.model_dump(by_alias=True),
          to=to)

      # 완료 상태 전송
      await send_loading(Loading(status="done"))

      print(f"[{self.namespace}] room 응답 결과: {responses}")

    @sio.event(namespace=self.namespace)
    async def query_radiology_analysis(sid: str, to: str, data: SummarizePatientRequest):
      """방사선 판독 분석만 단독으로 쿼리"""
      print(f"[{self.namespace}] query_radiology_analysis - sid: {sid}, patient_id: {to}")

      # === 로딩 상태 전송 함수 정의 ===
      async def send_loading(loading: Loading) -> None:
        """로딩 상태 전송"""
        await self.emit("loading", loading.to_json(), room=to)

      await send_loading(Loading(status="processing"))

      try:
        result = await medical_graph.workflow.ainvoke({
            "send_loading": send_loading,
            "data": data
        })

        # 방사선 분석 결과만 추출
        radiology_summary = result.get('radiology_summary')
        radiology_progression = result.get('radiology_progression')
        integrated_radiology = result.get('integrated_radiology_analysis')

        response = {
            "radiology_summary": radiology_summary.model_dump(by_alias=True) if radiology_summary else None,
            "radiology_progression": radiology_progression.model_dump(by_alias=True) if radiology_progression else None,
            "integrated_radiology_analysis": integrated_radiology.model_dump(by_alias=True) if integrated_radiology else None
        }

        await self.emit_with_ack(
            "query_radiology_analysis",
            response,
            to=to)

        await send_loading(Loading(status="done"))

      except Exception as e:
        print(f"[{self.namespace}] query_radiology_analysis 오류: {str(e)}")
        await self.emit("error", {"message": str(e)}, room=to)
