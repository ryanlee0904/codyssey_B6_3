"""주문 화면 + 상태 변경 (보호 경로: /app/orders/**, /app/sales)."""
from collections.abc import Callable

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import login_required
from app.core.database import get_db
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.core.flash import flash
from app.core.templating import render
from app.models import OrderStatus, User
from app.services import order_service

router = APIRouter(prefix="/app", tags=["orders"], dependencies=[Depends(login_required)])


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/orders")
def my_orders(request: Request, status_filter: str = "", user: User = Depends(login_required),
              db: Session = Depends(get_db)):
    selected = OrderStatus(status_filter) if status_filter in OrderStatus.__members__ else None
    orders = order_service.list_my_orders(db, user, selected)
    return render(request, "orders/list.html", {"orders": orders, "selected": selected})


@router.post("/orders")
def create_order(
    request: Request,
    goods_id: int = Form(...),
    quantity: int = Form(1),
    user: User = Depends(login_required),
    db: Session = Depends(get_db),
):
    try:
        order = order_service.place_order(db, user, goods_id, quantity)
    except (NotFoundError, PermissionDeniedError):
        raise
    except BusinessError as e:
        flash(request, e.message, "error")
        return _redirect(f"/app/goods/{goods_id}")
    flash(request, f"주문 #{order.id}이(가) 접수되었습니다. (상태: {order.status.label})", "success")
    return _redirect(f"/app/orders/{order.id}")


@router.get("/orders/{order_id}")
def order_detail(request: Request, order_id: int, user: User = Depends(login_required),
                 db: Session = Depends(get_db)):
    order = order_service.get_order_for_view(db, user, order_id)
    return render(request, "orders/detail.html", {"order": order})


def _change_status(request: Request, action: Callable, db: Session, user: User, order_id: int):
    """상태 변경 공통 처리: 성공 시 '변경 전 → 변경 후' 메시지, 실패 시 사유 메시지."""
    try:
        change = action(db, user, order_id)
    except (NotFoundError, PermissionDeniedError):
        raise
    except BusinessError as e:
        flash(request, e.message, "error")
    else:
        flash(request, change.message, "success")
    return _redirect(f"/app/orders/{order_id}")


@router.post("/orders/{order_id}/cancel")
def cancel_order(request: Request, order_id: int, user: User = Depends(login_required),
                 db: Session = Depends(get_db)):
    return _change_status(request, order_service.cancel_order, db, user, order_id)


@router.post("/orders/{order_id}/ship")
def ship_order(request: Request, order_id: int, user: User = Depends(login_required),
               db: Session = Depends(get_db)):
    return _change_status(request, order_service.ship_order, db, user, order_id)


@router.post("/orders/{order_id}/deliver")
def confirm_delivery(request: Request, order_id: int, user: User = Depends(login_required),
                     db: Session = Depends(get_db)):
    return _change_status(request, order_service.confirm_delivery, db, user, order_id)


@router.get("/sales")
def my_sales(request: Request, user: User = Depends(login_required), db: Session = Depends(get_db)):
    """판매 관리: 내가 등록한 상품에 들어온 주문 목록."""
    return render(request, "orders/sales.html", {"orders": order_service.list_my_sales(db, user)})
