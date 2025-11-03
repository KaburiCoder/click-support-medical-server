from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import sys
from src.api.main import api_router
from src.core.exceptions.handlers import register_exception_handlers

if sys.platform != "win32":
  import asyncio
  import uvloop
  asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
  # 시작할 때 리소스 초기화
  print("애플리케이션 시작: 모델 로딩 중...")

  yield  # FastAPI 애플리케이션 실행

  # 종료할 때 리소스 정리
  print("애플리케이션 종료: 리소스 정리 중...")
  print("정리 완료")

app = FastAPI(
    title="프로젝트 이름",
    description="프로젝트 설명",
    version="0.0.1",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler 등록
register_exception_handlers(app)

app.include_router(router=api_router, prefix="/api")
