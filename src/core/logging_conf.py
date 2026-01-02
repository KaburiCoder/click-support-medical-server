import os

def formatter(record):
    # 전체 경로에서 현재 작업 디렉토리 경로를 제거하여 상대 경로 추출
    rel_path = os.path.relpath(record["file"].path, os.getcwd())
    
    # 출력할 포맷 문자열 구성
    # {extra[rel_path]} 부분을 통해 아래에서 추가할 상대경로를 사용함
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        f"<cyan>{rel_path}</cyan>:<cyan>{{line}}</cyan> - "  # 상대 경로와 라인 번호
        "<level>{message}</level>\n"
    )
    return format_str

def setup_loguru():
  """Loguru 로깅 설정"""
  from loguru import logger
  import sys

  logger.remove()  # 기본 핸들러 제거
  logger.add(
      sys.stdout,
      format=formatter,
      level="DEBUG",
  )
