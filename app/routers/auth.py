"""로그인 / 회원가입 / 로그아웃 (공개 경로)."""
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional, login_user, logout_user, safe_redirect_path
from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.core.flash import flash
from app.core.templating import render
from app.models import User
from app.services import auth_service

router = APIRouter(tags=["auth"], dependencies=[Depends(get_current_user_optional)])


def _redirect(url: str) -> RedirectResponse:
    # 303: POST 처리 후 GET 으로 이동 (새로고침 시 폼 재전송 방지, PRG 패턴)
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_page(request: Request, next: str = "", user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        return _redirect(safe_redirect_path(next))
    return render(request, "auth/login.html", {"next": safe_redirect_path(next), "username": ""})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    # 폼 필드명(username/password)은 OAuth2PasswordRequestForm 규격과 동일하게 맞췄다.
    # 빈 값도 422 JSON 이 아니라 화면 안의 에러 메시지로 보여주기 위해 Form("") 로 직접 받는다.
    next_url = safe_redirect_path(next)
    user = auth_service.authenticate(db, username, password) if username and password else None

    if user is None:
        error = "아이디와 비밀번호를 모두 입력해 주세요." if not (username and password) \
            else "아이디 또는 비밀번호가 올바르지 않습니다."
        return render(
            request,
            "auth/login.html",
            {"error": error, "username": username, "next": next_url},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    login_user(request, user)
    flash(request, f"로그인 성공! {user.nickname}님 환영합니다.", "success")
    return _redirect(next_url)


@router.post("/logout")
def logout(request: Request):
    logout_user(request)
    flash(request, "로그아웃되었습니다.", "info")
    return _redirect("/")


@router.get("/signup")
def signup_page(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        return _redirect("/app/goods")
    return render(request, "auth/signup.html", {"form": {}})


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(""),
    nickname: str = Form(""),
    password: str = Form(""),
    password_confirm: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        auth_service.signup(db, username, nickname, password, password_confirm)
    except BusinessError as e:
        return render(
            request,
            "auth/signup.html",
            {"error": e.message, "form": {"username": username, "nickname": nickname}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    flash(request, "회원가입이 완료되었습니다. 로그인해 주세요.", "success")
    return _redirect("/login")
