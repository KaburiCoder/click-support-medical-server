"""Socket.IO 네임스페이스 기본 클래스"""
from typing import Optional, Any
from abc import ABC, abstractmethod
from src.sio.config import sio


class BaseNamespace(ABC):
  """Socket.IO 네임스페이스의 기본 클래스"""

  namespace: str = "/"

  @abstractmethod
  def register_events(self) -> None:
    """네임스페이스에 이벤트를 등록합니다"""
    pass

  # ========== Broadcast 메서드 ==========

  async def emit_to_namespace(
      self,
      event: str,
      data: dict,
      skip_sid: Optional[str] = None
  ) -> None:
    """네임스페이스의 모든 클라이언트에게 메시지 전송"""
    await sio.emit(event, data, skip_sid=skip_sid, namespace=self.namespace)

  async def emit(
      self,
      event: str,
      data: dict,
      room: Optional[str] = None,
      skip_sid: Optional[str] = None
  ) -> None:
    """room 또는 전체 네임스페이스에 메시지 전송"""
    await sio.emit(event, data, room=room, skip_sid=skip_sid, namespace=self.namespace)

  # ========== Room 관리 메서드 ==========

  async def enter_room(self, sid: str, room: str) -> None:
    """클라이언트를 룸에 추가"""
    await sio.enter_room(sid, room, namespace=self.namespace)

  async def leave_room(self, sid: str, room: str) -> None:
    """클라이언트를 룸에서 제거"""
    await sio.leave_room(sid, room, namespace=self.namespace)

  # ========== 개별 클라이언트 메서드 ==========

  async def emit_to_client(self, event: str, data: dict, to: str) -> None:
    """특정 클라이언트에게 메시지 전송"""
    await sio.emit(event, data, to=to, namespace=self.namespace)

  async def emit_with_ack(
      self,
      event: str,
      data: Any,
      to: str,
      timeout: int = 10
  ) -> Any:
    """클라이언트 또는 room에 메시지를 보내고 응답(acknowledgment)을 대기
    
    Args:
        event: 이벤트 이름
        data: 전송할 데이터
        to: 클라이언트 SID 또는 room 이름
        timeout: 응답 대기 시간(초)
        
    Returns:
        개별 응답 또는 {sid: response} 딕셔너리
    """
    try:
      response = await sio.call(
        event, 
        data, 
        to=to, 
        namespace=self.namespace, 
        timeout=timeout,        
      )
      return response
    except Exception as e:
      print(f"[{self.namespace}] emit_with_ack 오류 - event: {event}, to: {to}, error: {e}")
      raise