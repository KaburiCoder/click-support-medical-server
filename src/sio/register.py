"""Socket.IO 네임스페이스 등록"""

import sys
from src.sio import DefaultNamespace, MedicalNamespace
from src.sio.base import BaseNamespace
from loguru import logger
 
def register_all_namespaces() -> None:
  """모든 네임스페이스 등록"""
  namespaces: list[BaseNamespace] = [
      DefaultNamespace(),
      MedicalNamespace(),
  ]

  for ns in namespaces:
    ns.register_events()
    logger.info(f"네임스페이스 등록됨: {ns.namespace}")
