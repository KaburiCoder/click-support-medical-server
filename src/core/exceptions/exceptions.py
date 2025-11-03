from typing import Optional


class AppException(Exception):
  """애플리케이션 기본 Exception 클래스"""

  def __init__(
      self,
      message: str,
      status_code: int = 500,
      error_code: str = "INTERNAL_ERROR",
      details: Optional[dict] = None,
  ):
    self.message = message
    self.status_code = status_code
    self.error_code = error_code
    self.details = details or {}
    super().__init__(self.message)


class ValidationException(AppException):
  """입력 데이터 검증 실패"""

  def __init__(self, message: str, details: Optional[dict] = None):
    super().__init__(
        message=message,
        status_code=422,
        error_code="VALIDATION_ERROR",
        details=details,
    )


class NotFound(AppException):
  """리소스를 찾을 수 없음"""

  def __init__(self, message: str, resource: Optional[str] = None):
    details = {"resource": resource} if resource else {}
    super().__init__(
        message=message,
        status_code=404,
        error_code="NOT_FOUND",
        details=details,
    )


class UnauthorizedException(AppException):
  """인증 실패"""

  def __init__(self, message: str = "인증이 필요합니다"):
    super().__init__(
        message=message,
        status_code=401,
        error_code="UNAUTHORIZED",
    )


class ForbiddenException(AppException):
  """권한 부족"""

  def __init__(self, message: str = "접근 권한이 없습니다"):
    super().__init__(
        message=message,
        status_code=403,
        error_code="FORBIDDEN",
    )


class ConflictException(AppException):
  """리소스 충돌 (예: 중복된 데이터)"""

  def __init__(self, message: str, resource: Optional[str] = None):
    details = {"resource": resource} if resource else {}
    super().__init__(
        message=message,
        status_code=409,
        error_code="CONFLICT",
        details=details,
    )


class InternalServerError(AppException):
  """내부 서버 에러"""

  def __init__(self, message: str = "내부 서버 에러가 발생했습니다"):
    super().__init__(
        message=message,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
    )


class ExternalServiceError(AppException):
  """외부 서비스 호출 실패"""

  def __init__(self, service_name: str, message: Optional[str] = None):
    error_msg = message or f"{service_name} 서비스 호출에 실패했습니다"
    super().__init__(
        message=error_msg,
        status_code=502,
        error_code="EXTERNAL_SERVICE_ERROR",
        details={"service": service_name},
    )
