from src.sio.config import sio
from src.sio.base import BaseNamespace


class DefaultNamespace(BaseNamespace):
  """기본 네임스페이스 - 모든 기본 통신을 처리합니다"""

  namespace = "/"

  def register_events(self) -> None:
    """기본 네임스페이스 이벤트 등록"""  

    @sio.event(namespace=self.namespace)
    async def connect(sid: str, environ: dict):
      """클라이언트가 기본 네임스페이스에 연결"""
      print(f"[{self.namespace}] 클라이언트 연결: {sid}")