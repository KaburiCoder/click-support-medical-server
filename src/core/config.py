from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  debug: bool = False
  APP_ENV:  str | None = None
  DATABASE_URL: str = ""

  model_config = {
      "env_file": ".env",
      "extra": "ignore"  # 정의되지 않은 환경 변수 무시
  }


settings = Settings()
