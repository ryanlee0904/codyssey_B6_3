from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.goods import Goods
    from app.models.order import Order


class User(Base):
    """회원. 구매자이면서 동시에 상품을 등록하는 판매자가 될 수 있다."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # 로그인 ID
    password_hash: Mapped[str] = mapped_column(String(100))  # bcrypt 해시 (평문 저장 X)
    nickname: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # ── 연관관계 1) User(1) : Order(N) — 양방향 (Order.buyer 와 back_populates) ──
    # [삭제 정책] cascade="all, delete-orphan"
    # 이유: 주문 내역은 구매자 개인에게 귀속된 데이터다. 회원이 탈퇴(삭제)하면
    #       구매자 없는 주문은 의미가 없고, 개인정보 파기 관점에서도 함께 지워야 한다.
    #       또한 user.orders 컬렉션에서 빠진 주문(orphan)도 DB에서 삭제되도록 한다.
    orders: Mapped[list[Order]] = relationship(
        back_populates="buyer",
        cascade="all, delete-orphan",
        order_by="Order.id.desc()",
    )

    # ── 연관관계 2) User(1) : Goods(N) — 양방향 (Goods.seller 와 back_populates) ──
    # [삭제 정책] cascade 없음 + passive_deletes="all" + FK ondelete="RESTRICT" (수동 처리)
    # 이유: 판매자의 상품에는 "다른 회원들의 주문"이 매달려 있다. 판매자 삭제와 함께
    #       상품을 지워버리면 남의 주문 이력까지 깨진다. 따라서 상품이 남아 있는 회원은
    #       DB 차원에서 삭제를 막고(RESTRICT), 상품 정리를 먼저 하도록 한다.
    goods: Mapped[list[Goods]] = relationship(
        back_populates="seller",
        passive_deletes="all",
        order_by="Goods.id.desc()",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"
