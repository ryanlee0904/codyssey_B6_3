from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class Goods(Base):
    """판매 상품."""

    __tablename__ = "goods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)  # 원 단위
    stock: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # N:1 — 여러 상품이 한 판매자(User)에 속한다.
    # ondelete="RESTRICT": 상품이 남아 있는 판매자는 삭제할 수 없다. (User.goods 주석 참고)
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), index=True)
    seller: Mapped[User] = relationship(back_populates="goods")

    # ── 연관관계 3) Goods(1) : Order(N) — 양방향 (Order.goods 와 back_populates) ──
    # [삭제 정책] cascade 없음 + passive_deletes="all" + FK ondelete="RESTRICT" (수동 처리)
    # 이유: 주문은 거래(결제) 기록이므로 상품이 지워져도 사라지면 안 된다.
    #       그래서 cascade 삭제를 쓰지 않고, 주문 이력이 있는 상품은 삭제를 막는다.
    #       - 서비스 계층(goods_service.delete_goods)에서 먼저 검사해 친절한 메시지를 보여주고
    #       - DB의 RESTRICT 제약이 최종 안전장치 역할을 한다.
    #       (주문 이력이 없는 상품만 실제로 삭제된다.)
    orders: Mapped[list[Order]] = relationship(
        back_populates="goods",
        passive_deletes="all",
        order_by="Order.id.desc()",
    )

    @property
    def is_sold_out(self) -> bool:
        return self.stock <= 0

    def __repr__(self) -> str:
        return f"<Goods id={self.id} name={self.name!r}>"
