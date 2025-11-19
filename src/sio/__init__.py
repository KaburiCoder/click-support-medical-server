"""Socket.IO 설정 및 네임스페이스 관리"""
from .config import sio, get_socketio_app
from .base import BaseNamespace
from .features.default import DefaultNamespace
from .features.medical import MedicalNamespace
from .register import register_all_namespaces

__all__ = [
    "sio",
    "get_socketio_app",
    "BaseNamespace",
    "DefaultNamespace",
    "MedicalNamespace",
    "register_all_namespaces",
]
