"""
FastAPI 전역 Exception Handler
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.exceptions import AppException
from loguru import logger


def register_exception_handlers(app: FastAPI) -> None:
  """FastAPI 애플리케이션에 모든 Exception Handler 등록"""

  @app.exception_handler(AppException)
  async def app_exc_handler(request: Request, exc: AppException):
    logger.error(
        f"AppException: {exc.error_code} - {exc.message}",
        extra={"status_code": exc.status_code, "details": exc.details},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )

  @app.exception_handler(StarletteHTTPException)
  async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {},
            },
        },
    )

  @app.exception_handler(Exception)
  async def generic_exc_handler(request: Request, exc: Exception):
    logger.exception(
        f"Unexpected exception: {type(exc).__name__} - {str(exc)}",
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "내부 서버 에러가 발생했습니다",
                "details": {},
            },
        },
    )
