"""Order 데이터 접근."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Goods, Order, OrderStatus


def get_detail(db: Session, order_id: int) -> Optional[Order]:
    """주문 상세: 주문자(N:1), 상품(N:1), 상품의 판매자까지 로드."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            joinedload(Order.buyer),
            joinedload(Order.goods).joinedload(Goods.seller),
        )
    )
    return db.scalar(stmt)


def list_by_buyer(db: Session, buyer_id: int, status: Optional[OrderStatus] = None) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.buyer_id == buyer_id)
        .options(joinedload(Order.goods).joinedload(Goods.seller))
        .order_by(Order.id.desc())
    )
    if status is not None:
        stmt = stmt.where(Order.status == status)
    return list(db.scalars(stmt))


def list_by_seller(db: Session, seller_id: int) -> list[Order]:
    """내가 등록한 상품에 들어온 주문 (Order → Goods → seller 조인)."""
    stmt = (
        select(Order)
        .join(Order.goods)
        .where(Goods.seller_id == seller_id)
        .options(joinedload(Order.goods), joinedload(Order.buyer))
        .order_by(Order.id.desc())
    )
    return list(db.scalars(stmt))


def add(db: Session, order: Order) -> Order:
    db.add(order)
    return order
