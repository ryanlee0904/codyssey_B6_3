"""Jinja2 템플릿 설정과 공통 렌더링 함수."""
from typing import Optional
from datetime import datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import BASE_DIR, settings
from app.core.flash import pop_flashes
from app.models.order import OrderStatus

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _won(value: Optional[int]) -> str:
    return f"{value or 0:,}원"


def _dt(value: Optional[datetime]) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


templates.env.filters["won"] = _won
templates.env.filters["dt"] = _dt
templates.env.globals["OrderStatus"] = OrderStatus
templates.env.globals["APP_NAME"] = settings.APP_NAME


def render(request: Request, name: str, context: Optional[dict] = None, status_code: int = 200):
    """모든 화면이 공통으로 쓰는 렌더 함수.

    - current_user: auth 의존성(get_current_user_optional)이 request.state에 넣어둔 로그인 사용자.
      base.html은 이 값으로 [로그인] / [OOO님 환영합니다 + 로그아웃] 을 나눠 그린다.
    - flashes: 직전 요청에서 남긴 안내 메시지
    """
    ctx = {
        "current_user": getattr(request.state, "user", None),
        "flashes": pop_flashes(request),
    }
    if context:
        ctx.update(context)
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
