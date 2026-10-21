"""공개 페이지 (로그인 불필요)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.core.database import get_db
from app.core.templating import render
from app.services import goods_service

# 공개 라우터: 로그인 여부만 확인(UI 분기용)하고 막지는 않는다.
router = APIRouter(tags=["public"], dependencies=[Depends(get_current_user_optional)])


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    return render(request, "index.html", {"latest_goods": goods_service.latest_goods(db)})
