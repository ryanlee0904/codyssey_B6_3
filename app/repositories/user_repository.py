"""User 데이터 접근. (조회/저장만 담당, 비즈니스 규칙과 commit은 서비스 계층 책임)"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Goods, Order, User


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def get_by_username(db: Session, username: str) -> Optional[User]:
    return db.scalar(select(User).where(User.username == username))


def get_with_relations(db: Session, user_id: int) -> Optional[User]:
    """마이페이지용: 회원 + 주문(상품 포함) + 등록 상품을 한 번에 로드."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.orders).selectinload(Order.goods),
            selectinload(User.goods).selectinload(Goods.orders),
        )
        .execution_options(populate_existing=True)
    )
    return db.scalar(stmt)


def add(db: Session, user: User) -> User:
    db.add(user)
    return user
