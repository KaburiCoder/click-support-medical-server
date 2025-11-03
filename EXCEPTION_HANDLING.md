# 전역 Exception 처리 구조

FastAPI 프로젝트에 일관된 예외 처리를 제공하는 전역 Exception 구조입니다.

## 📁 파일 구조

```
src/
├── core/
│   ├── exceptions.py          # 커스텀 Exception 클래스 정의
│   ├── handlers.py             # Exception Handler 등록
│   ├── exception_examples.py   # 사용 예시
│   └── config.py
└── main.py                     # Exception Handler 등록 (app 초기화)
```

## 🎯 사용 가능한 Exception 클래스

### 1. `AppException` (기본 Exception)
모든 커스텀 Exception의 부모 클래스입니다.

```python
raise AppException(
    message="에러 메시지",
    status_code=500,
    error_code="CUSTOM_ERROR",
    details={"key": "value"}
)
```

### 2. `ValidationException` (입력 검증 실패)
상태코드: **422**

```python
raise ValidationException(
    message="이메일 형식이 올바르지 않습니다",
    details={"field": "email"}
)
```

### 3. `NotFound` (리소스를 찾을 수 없음)
상태코드: **404**

```python
raise NotFound(
    message="사용자를 찾을 수 없습니다",
    resource="User"
)
```

### 4. `UnauthorizedException` (인증 실패)
상태코드: **401**

```python
raise UnauthorizedException("인증이 필요합니다")
```

### 5. `ForbiddenException` (권한 부족)
상태코드: **403**

```python
raise ForbiddenException("접근 권한이 없습니다")
```

### 6. `ConflictException` (리소스 충돌/중복)
상태코드: **409**

```python
raise ConflictException(
    message="이미 존재하는 이메일입니다",
    resource="User"
)
```

### 7. `InternalServerError` (내부 서버 에러)
상태코드: **500**

```python
raise InternalServerError("내부 서버 에러가 발생했습니다")
```

### 8. `ExternalServiceError` (외부 서비스 호출 실패)
상태코드: **502**

```python
raise ExternalServiceError(
    service_name="OpenAI API",
    message="API 호출 시간 초과"
)
```

## 📝 Response 형식

### ✅ 에러 응답 (Exception 발생 시)

모든 Exception은 다음과 같은 형식으로 응답됩니다:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {
      "additional": "information"
    }
  }
}
```

### 예시

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "이메일 형식이 올바르지 않습니다",
    "details": {
      "field": "email"
    }
  }
}
```

## 🚀 FastAPI 라우트에서 사용하기

```python
from fastapi import APIRouter
from pydantic import BaseModel
from src.core.exceptions import ValidationException, NotFound, ConflictException

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    name: str

@router.post("/users")
async def create_user(user: UserCreate):
    # 입력 검증
    if "@" not in user.email:
        raise ValidationException(
            message="유효한 이메일을 입력해주세요",
            details={"field": "email"}
        )
    
    # 중복 체크
    existing_user = db.query(User).filter_by(email=user.email).first()
    if existing_user:
        raise ConflictException(
            message="이미 존재하는 이메일입니다",
            resource="User"
        )
    
    # 비즈니스 로직
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    
    return {"success": True, "data": new_user}

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise NotFound(
            message=f"ID {user_id}인 사용자를 찾을 수 없습니다",
            resource="User"
        )
    
    return {"success": True, "data": user}
```

## 🔧 Handler 구동 방식

Exception Handler는 `src/main.py`에서 자동으로 등록됩니다:

```python
from src.core.handlers import register_exception_handlers

# ...

# Exception Handler 등록
register_exception_handlers(app)
```

### Handler의 역할

1. **AppException 처리**: 커스텀 Exception을 처리하고 정의된 상태코드와 에러코드로 응답
2. **HTTPException 처리**: FastAPI 기본 예외를 처리
3. **일반 Exception 처리**: 예상하지 못한 에러를 로깅하고 안전하게 응답
   - 개발 환경 (`debug=True`): 상세 에러 정보 반환
   - 프로덕션 환경 (`debug=False`): 일반 메시지만 반환

## 🔍 디버그 모드

`src/core/config.py`에서 `debug` 설정으로 상세 정보 노출 여부를 제어합니다:

```python
class Settings(BaseSettings):
    debug: bool = False  # False = 프로덕션 (일반 메시지만)
    # ...
```

## 📊 로깅

모든 Exception은 자동으로 로깅됩니다:

- **AppException**: `logger.error()` - 에러 수준
- **HTTPException**: `logger.warning()` - 경고 수준
- **일반 Exception**: `logger.exception()` - 상세 스택 트레이스 포함

## ✨ 장점

- ✅ **일관된 에러 응답**: 모든 API 에러가 동일한 형식으로 응답
- ✅ **자동 로깅**: 모든 Exception이 자동으로 로깅됨
- ✅ **타입 안전**: Python 타입 힌트 지원
- ✅ **확장성**: 새로운 Exception을 쉽게 추가 가능
- ✅ **환경별 응답**: 개발/프로덕션 환경에 따른 상이한 응답
