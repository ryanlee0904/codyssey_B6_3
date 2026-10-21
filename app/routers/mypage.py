"""마이페이지 (보호 경로: /app/me) — 회원과 연관된 주문/상품 목록 출력."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import login_required
from app.core.database import get_db
from app.core.templating import render
from app.models import User
from app.services import user_service

router = APIRouter(prefix="/app", tags=["mypage"], dependencies=[Depends(login_required)])


@router.get("/me")
def my_page(request: Request, user: User = Depends(login_required), db: Session = Depends(get_db)):
    summary = user_service.get_my_page(db, user.id)
    return render(request, "mypage.html", {"summary": summary})
