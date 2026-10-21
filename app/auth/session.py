"""세션 기반 로그인 상태 관리.

로그인 성공 시 서명된 세션 쿠키(starlette SessionMiddleware)에 user_id 만 저장한다.
비밀번호나 개인정보는 쿠키에 넣지 않는다.
"""
from typing import Optional
from fastapi import Request

from app.models import User

SESSION_USER_KEY = "user_id"
DEFAULT_AFTER_LOGIN = "/app/goods"


def login_user(request: Request, user: User) -> None:
    # 세션 고정 공격 방지: 로그인 시 기존 세션 내용을 비우고 새로 기록
    request.session.clear()
    request.session[SESSION_USER_KEY] = user.id


def logout_user(request: Request) -> None:
    request.session.clear()


def get_session_user_id(request: Request) -> Optional[int]:
    return request.session.get(SESSION_USER_KEY)


def safe_redirect_path(next_url: Optional[str]) -> str:
    """로그인 후 이동 경로 검증. 외부 사이트로 튕기는 open redirect 를 막는다."""
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return DEFAULT_AFTER_LOGIN
