from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.goods import Goods
    from app.models.user import User


class OrderStatus(str, enum.Enum):
    """주문 상태.

    주문접수(ORDERED) ──▶ 배송중(SHIPPING) ──▶ 배송완료(DELIVERED)
          │
          └──▶ 주문취소(CANCELLED)
    """

    ORDERED = "ORDERED"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]

    def can_change_to(self, target: OrderStatus) -> bool:
        return target in ALLOWED_TRANSITIONS[self]


_STATUS_LABELS = {
    OrderStatus.ORDERED: "주문접수",
    OrderStatus.SHIPPING: "배송중",
    OrderStatus.DELIVERED: "배송완료",
    OrderStatus.CANCELLED: "주문취소",
}

# 허용되는 상태 전이 표. 여기에 없는 변경은 서비스 계층에서 거부된다.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.ORDERED: {OrderStatus.SHIPPING, OrderStatus.CANCELLED},
    OrderStatus.SHIPPING: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),  # 최종 상태
    OrderStatus.CANCELLED: set(),  # 최종 상태
}


class Order(Base):
    """주문 1건 = 한 회원이 한 상품을 N개 주문한 기록.

    User 와 Goods 사이의 N:M(회원이 여러 상품을, 상품이 여러 회원에게) 관계를
    이 중간 모델로 풀어서 User 1:N Order N:1 Goods 형태로 표현한다.
    """

    __tablename__ = "order_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    # 주문 시점 단가 스냅샷: 나중에 상품 가격이 바뀌어도 주문 금액은 변하지 않아야 한다.
    unit_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.ORDERED,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # N:1 — 주문자. 회원 삭제 시 주문도 함께 삭제 (User.orders 의 cascade 주석 참고)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    buyer: Mapped[User] = relationship(back_populates="orders")

    # N:1 — 주문 상품. 주문이 있는 상품은 삭제 불가 (Goods.orders 주석 참고)
    goods_id: Mapped[int] = mapped_column(ForeignKey("goods.id", ondelete="RESTRICT"), index=True)
    goods: Mapped[Goods] = relationship(back_populates="orders")

    @property
    def total_price(self) -> int:
        return self.unit_price * self.quantity

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status.value}>"
