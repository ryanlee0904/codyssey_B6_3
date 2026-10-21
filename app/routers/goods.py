"""상품 화면 (보호 경로: /app/goods/**)."""
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import login_required
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.core.flash import flash
from app.core.templating import render
from app.models import User
from app.services import goods_service

# 라우터 단위로 login_required 를 걸어, 아래 모든 경로가 로그인 필수가 된다.
router = APIRouter(prefix="/app/goods", tags=["goods"], dependencies=[Depends(login_required)])


@router.get("")
def goods_list(request: Request, db: Session = Depends(get_db)):
    return render(request, "goods/list.html", {"goods_list": goods_service.list_goods(db)})


@router.get("/new")
def goods_new_page(request: Request):
    return render(request, "goods/new.html", {"form": {}})


@router.post("/new")
def goods_create(
    request: Request,
    name: str = Form(""),
    description: str = Form(""),
    price: int = Form(0),
    stock: int = Form(0),
    user: User = Depends(login_required),
    db: Session = Depends(get_db),
):
    try:
        goods = goods_service.register_goods(db, user, name, description, price, stock)
    except BusinessError as e:
        form = {"name": name, "description": description, "price": price, "stock": stock}
        return render(request, "goods/new.html", {"error": e.message, "form": form},
                      status_code=status.HTTP_400_BAD_REQUEST)
    flash(request, f"상품 '{goods.name}'이(가) 등록되었습니다.", "success")
    return RedirectResponse(f"/app/goods/{goods.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{goods_id}")
def goods_detail(request: Request, goods_id: int, db: Session = Depends(get_db)):
    goods = goods_service.get_goods_detail(db, goods_id)
    return render(request, "goods/detail.html", {"goods": goods})


@router.post("/{goods_id}/delete")
def goods_delete(request: Request, goods_id: int, user: User = Depends(login_required),
                 db: Session = Depends(get_db)):
    try:
        name = goods_service.delete_goods(db, user, goods_id)
    except (NotFoundError, PermissionDeniedError):
        raise  # 404/403 페이지는 main.py 의 공통 핸들러가 처리
    except BusinessError as e:
        flash(request, e.message, "error")
        return RedirectResponse(f"/app/goods/{goods_id}", status_code=status.HTTP_303_SEE_OTHER)
    flash(request, f"상품 '{name}'이(가) 삭제되었습니다.", "success")
    return RedirectResponse("/app/goods", status_code=status.HTTP_303_SEE_OTHER)
