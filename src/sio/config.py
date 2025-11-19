"""Socket.IO 설정 및 초기화"""
from fastapi import FastAPI
from socketio import ASGIApp, AsyncServer

# Socket.IO 인스턴스 생성

# mgr = AsyncRedisManager('redis://localhost:6379/0')
sio = AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["*"],
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    # client_manager=mgr,  # Redis 매니저 사용 시 주석 해제
)


def get_socketio_app(app: FastAPI) -> ASGIApp:
  """
  FastAPI 앱과 Socket.IO를 통합하여 ASGI 앱 반환

  Args:
      app: FastAPI 애플리케이션

  Returns:
      Socket.IO와 통합된 ASGI 앱
  """
  socketio_app = ASGIApp(sio, app, socketio_path="/socket.io")
  return socketio_app
