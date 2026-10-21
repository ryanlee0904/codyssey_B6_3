"""Goods 데이터 접근."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Goods, Order


def get_by_id(db: Session, goods_id: int) -> Optional[Goods]:
    return db.get(Goods, goods_id)


def get_detail(db: Session, goods_id: int) -> Optional[Goods]:
    """상품 상세: 판매자(N:1) + 이 상품의 주문 목록(1:N)과 각 주문자까지 로드."""
    stmt = (
        select(Goods)
        .where(Goods.id == goods_id)
        .options(
            joinedload(Goods.seller),
            selectinload(Goods.orders).joinedload(Order.buyer),
        )
    )
    return db.scalar(stmt)


def list_all(db: Session) -> list[Goods]:
    stmt = select(Goods).options(joinedload(Goods.seller)).order_by(Goods.id.desc())
    return list(db.scalars(stmt))


def list_latest(db: Session, limit: int = 4) -> list[Goods]:
    stmt = select(Goods).options(joinedload(Goods.seller)).order_by(Goods.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def has_orders(db: Session, goods_id: int) -> bool:
    return db.scalar(select(Order.id).where(Order.goods_id == goods_id).limit(1)) is not None


def add(db: Session, goods: Goods) -> Goods:
    db.add(goods)
    return goods


def delete(db: Session, goods: Goods) -> None:
    db.delete(goods)
