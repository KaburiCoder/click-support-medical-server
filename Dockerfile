# 빌드 스테이지
FROM python:3.13-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache/

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 의존성만 먼저 설치 (캐시 최적화를 위해)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 소스 코드 복사 (필요한 파일만)
COPY src/ src/
COPY pyproject.toml uv.lock ./

# README.md가 없으면 빈 파일 생성
RUN test -f README.md || touch README.md

# 프로젝트 설치 (이때는 --no-build 사용하지 않음)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 프로덕션 스테이지
FROM python:3.13-slim AS production

# 비루트 사용자 생성 (보안 및 최적화)
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# uv 실행 파일 복사
COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /bin/uvx /bin/uvx

# 빌드 스테이지에서 필요한 파일만 복사
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "src.main:asgi_app", "--host", "0.0.0.0", "--port", "8000"]