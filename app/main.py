"""애플리케이션 진입점.

실행:  uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.auth import LoginRequiredException
from app.core.config import BASE_DIR, settings
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.flash import flash
from app.core.templating import render
from app.routers import auth, goods, mypage, orders, pages
from app.seed import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # 테이블 생성 + 테스트 계정/상품 시드
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# 세션 기반 인증: 서명된 쿠키에 user_id 저장 (itsdangerous 로 위변조 방지)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE,
    same_site="lax",
    https_only=False,  # 로컬 개발(http). 운영(https)에서는 True
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 공개 라우터
app.include_router(pages.router)
app.include_router(auth.router)
# 보호 라우터 (/app/**, 라우터 단위로 login_required 적용)
app.include_router(goods.router)
app.include_router(orders.router)
app.include_router(mypage.router)


# ── 예외 → 화면 처리 ────────────────────────────────────

@app.exception_handler(LoginRequiredException)
async def login_required_handler(request: Request, exc: LoginRequiredException):
    """비로그인 사용자가 보호 경로 접근 → 안내 메시지와 함께 로그인 페이지로 이동."""
    flash(request, "로그인이 필요한 페이지입니다. 로그인 후 이용해 주세요.", "warning")
    return RedirectResponse(f"/login?next={quote(exc.next_url, safe='/?=&')}",
                            status_code=status.HTTP_303_SEE_OTHER)


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    return render(request, "errors/error.html",
                  {"code": 403, "title": "접근 권한이 없습니다", "message": exc.message},
                  status_code=status.HTTP_403_FORBIDDEN)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return render(request, "errors/error.html",
                  {"code": 404, "title": "페이지를 찾을 수 없습니다", "message": exc.message},
                  status_code=status.HTTP_404_NOT_FOUND)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """존재하지 않는 URL 등 일반 HTTP 오류도 JSON 대신 화면으로 보여준다."""
    titles = {404: "페이지를 찾을 수 없습니다", 405: "허용되지 않은 요청입니다"}
    return render(request, "errors/error.html",
                  {"code": exc.status_code, "title": titles.get(exc.status_code, "오류가 발생했습니다"),
                   "message": str(exc.detail)},
                  status_code=exc.status_code)
