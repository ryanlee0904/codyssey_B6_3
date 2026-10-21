"""애플리케이션 설정.

환경 변수가 있으면 우선 사용하고, 없으면 로컬 개발용 기본값을 사용한다.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../app
PROJECT_DIR = BASE_DIR.parent  # 프로젝트 루트


class Settings:
    APP_NAME: str = "Mini Shop"

    # SQLite 파일은 프로젝트 루트에 생성된다. (PostgreSQL 사용 시 URL만 바꾸면 됨)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_DIR / 'shop.db'}")

    # 세션 쿠키 서명 키. 운영 환경에서는 반드시 환경 변수로 교체한다.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-secret-key-change-me")
    SESSION_COOKIE_NAME: str = "mini_shop_session"
    SESSION_MAX_AGE: int = 60 * 60 * 2  # 2시간


settings = Settings()
