"""회원(마이페이지) 비즈니스 로직."""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import OrderStatus, User
from app.repositories import user_repository


@dataclass(frozen=True)
class MyPageSummary:
    user: User
    order_count: int
    total_spent: int  # 취소 제외 구매 금액
    status_counts: dict[OrderStatus, int]


def get_my_page(db: Session, user_id: int) -> MyPageSummary:
    user = user_repository.get_with_relations(db, user_id)
    if user is None:
        raise NotFoundError("존재하지 않는 회원입니다.")

    # user.orders: User → Order 연관관계(1:N)를 통해 DB에서 조회된 주문 목록
    status_counts = {status: 0 for status in OrderStatus}
    for order in user.orders:
        status_counts[order.status] += 1
    total_spent = sum(o.total_price for o in user.orders if o.status != OrderStatus.CANCELLED)

    return MyPageSummary(
        user=user,
        order_count=len(user.orders),
        total_spent=total_spent,
        status_counts=status_counts,
    )
