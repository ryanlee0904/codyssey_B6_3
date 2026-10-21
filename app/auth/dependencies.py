"""인증/인가 의존성 (FastAPI Depends).

- get_current_user_optional : 공개 페이지용. 로그인했으면 User, 아니면 None.
                              request.state.user 에도 넣어 템플릿이 로그인 여부로 UI를 바꾸게 한다.
- login_required            : 보호 페이지용. 비로그인 시 LoginRequiredException 을 던지고,
                              main.py 의 예외 핸들러가 /login?next=원래경로 로 리다이렉트한다.

보호 라우터는 APIRouter(dependencies=[Depends(login_required)]) 로 선언해
라우터 아래 모든 경로(/app/**)가 자동으로 보호되도록 한다.
"""
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.session import SESSION_USER_KEY, get_session_user_id
from app.core.database import get_db
from app.models import User
from app.repositories import user_repository


class LoginRequiredException(Exception):
    """비로그인 사용자가 보호 경로에 접근했을 때 발생."""

    def __init__(self, next_url: str):
        self.next_url = next_url


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user = None
    user_id = get_session_user_id(request)
    if user_id is not None:
        user = user_repository.get_by_id(db, user_id)
        if user is None:
            # 세션에는 있는데 DB에 없는 사용자(삭제됨) → 세션 정리
            request.session.pop(SESSION_USER_KEY, None)
    request.state.user = user
    return user


def login_required(request: Request, user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if user is None:
        next_url = request.url.path
        if request.url.query:
            next_url += f"?{request.url.query}"
        # POST 요청(폼 제출)은 로그인 후 같은 주소로 GET 할 수 없으므로 목록으로 보낸다
        if request.method != "GET":
            next_url = "/app/goods"
        raise LoginRequiredException(next_url=next_url)
    return user
