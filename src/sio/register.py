"""Socket.IO 네임스페이스 등록"""

from src.sio import DefaultNamespace, MedicalNamespace
from src.sio.base import BaseNamespace


def register_all_namespaces() -> None:
  """모든 네임스페이스 등록"""
  namespaces: list[BaseNamespace] = [
      DefaultNamespace(),
      MedicalNamespace(),
  ]

  for ns in namespaces:
    ns.register_events()
    print(f"네임스페이스 등록됨: {ns.namespace}")
