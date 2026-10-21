"""주문 비즈니스 로직 — 이 프로젝트의 핵심 "상태 변경" 기능.

상태 전이 규칙 (models/order.py 의 ALLOWED_TRANSITIONS):
    주문접수 → 배송중   : 판매자가 [배송 시작]
    배송중   → 배송완료 : 구매자가 [수령 확인]
    주문접수 → 주문취소 : 구매자가 [주문 취소]  (재고 원복)
    배송중/배송완료/주문취소 상태에서는 취소 불가
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.models import Order, OrderStatus, User
from app.repositories import goods_repository, order_repository

MAX_QUANTITY_PER_ORDER = 99


@dataclass(frozen=True)
class StatusChange:
    """상태 변경 결과 (변경 전/후를 화면에 보여주기 위해 반환)."""

    order: Order
    before: OrderStatus
    after: OrderStatus

    @property
    def message(self) -> str:
        return f"주문 #{self.order.id} 상태 변경: {self.before.label} → {self.after.label}"


# ── 조회 ──────────────────────────────────────────────

def get_order_for_view(db: Session, user: User, order_id: int) -> Order:
    """구매자 본인 또는 해당 상품의 판매자만 주문 상세를 볼 수 있다."""
    order = _get_order(db, order_id)
    if user.id not in (order.buyer_id, order.goods.seller_id):
        raise PermissionDeniedError("본인과 관련된 주문만 조회할 수 있습니다.")
    return order


def list_my_orders(db: Session, user: User, status: Optional[OrderStatus] = None) -> list[Order]:
    return order_repository.list_by_buyer(db, user.id, status)


def list_my_sales(db: Session, user: User) -> list[Order]:
    return order_repository.list_by_seller(db, user.id)


# ── 생성 ──────────────────────────────────────────────

def place_order(db: Session, buyer: User, goods_id: int, quantity: int) -> Order:
    goods = goods_repository.get_by_id(db, goods_id)
    if goods is None:
        raise NotFoundError("존재하지 않는 상품입니다.")
    if goods.seller_id == buyer.id:
        raise BusinessError("본인이 등록한 상품은 주문할 수 없습니다.")
    if not 1 <= quantity <= MAX_QUANTITY_PER_ORDER:
        raise BusinessError(f"주문 수량은 1~{MAX_QUANTITY_PER_ORDER}개입니다.")
    if goods.stock < quantity:
        raise BusinessError(f"재고가 부족합니다. (남은 재고: {goods.stock}개)")

    goods.stock -= quantity  # 재고 차감
    order = Order(
        buyer=buyer,
        goods=goods,
        quantity=quantity,
        unit_price=goods.price,  # 주문 시점 가격 고정
        status=OrderStatus.ORDERED,
    )
    order_repository.add(db, order)
    db.commit()
    return order


# ── 상태 변경 ──────────────────────────────────────────

def cancel_order(db: Session, user: User, order_id: int) -> StatusChange:
    order = _get_order(db, order_id)
    _ensure_buyer(order, user, "주문을 취소할 수 있는 사람은 구매자 본인뿐입니다.")

    change = _transition(order, OrderStatus.CANCELLED)
    order.cancelled_at = datetime.now()
    order.goods.stock += order.quantity  # 취소 시 재고 원복
    db.commit()
    return change


def ship_order(db: Session, user: User, order_id: int) -> StatusChange:
    order = _get_order(db, order_id)
    if order.goods.seller_id != user.id:
        raise PermissionDeniedError("배송 시작은 해당 상품의 판매자만 할 수 있습니다.")

    change = _transition(order, OrderStatus.SHIPPING)
    order.shipped_at = datetime.now()
    db.commit()
    return change


def confirm_delivery(db: Session, user: User, order_id: int) -> StatusChange:
    order = _get_order(db, order_id)
    _ensure_buyer(order, user, "수령 확인은 구매자 본인만 할 수 있습니다.")

    change = _transition(order, OrderStatus.DELIVERED)
    order.delivered_at = datetime.now()
    db.commit()
    return change


# ── 내부 헬퍼 ──────────────────────────────────────────

def _get_order(db: Session, order_id: int) -> Order:
    order = order_repository.get_detail(db, order_id)
    if order is None:
        raise NotFoundError("존재하지 않는 주문입니다.")
    return order


def _ensure_buyer(order: Order, user: User, message: str) -> None:
    if order.buyer_id != user.id:
        raise PermissionDeniedError(message)


def _transition(order: Order, target: OrderStatus) -> StatusChange:
    """허용된 전이인지 검사하고 상태를 바꾼다. 허용되지 않으면 BusinessError."""
    before = order.status
    if not before.can_change_to(target):
        raise BusinessError(f"'{before.label}' 상태의 주문은 '{target.label}'(으)로 변경할 수 없습니다.")
    order.status = target
    return StatusChange(order=order, before=before, after=target)
