"""Socket.IO 설정 및 초기화"""
from fastapi import FastAPI
from socketio import ASGIApp, AsyncServer

from src.core import config

# mgr = AsyncRedisManager('redis://localhost:6379/0')
sio = AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:3000",      # 로컬 개발용
        "http://localhost:5173",      # Vite 개발 서버
        "http://localhost:8000",      # 로컬 백엔드
        "https://support.click-soft.co.kr",  # 프로덕션
    ],
    cors_credentials=True,
    logger=config.settings.debug,
    ping_timeout=60,
    ping_interval=25,
    # client_manager=mgr,  # Redis 매니저 사용 시 주석 해제
)


def get_socketio_app(app: FastAPI) -> ASGIApp:
  """FastAPI 앱과 Socket.IO를 통합하여 ASGI 앱 반환.

  Args:
      app: FastAPI 애플리케이션

  Returns:
      Socket.IO와 통합된 ASGI 앱
  """
  # Ingress가 /medical-api prefix를 유지한 채로 전달하므로, 전체 경로를 맞춰준다.
  return ASGIApp(sio, app, socketio_path="/medical-api/socket.io")
