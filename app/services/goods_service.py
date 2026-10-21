"""상품 비즈니스 로직."""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.models import Goods, User
from app.repositories import goods_repository


def list_goods(db: Session) -> list[Goods]:
    return goods_repository.list_all(db)


def latest_goods(db: Session, limit: int = 4) -> list[Goods]:
    return goods_repository.list_latest(db, limit)


def get_goods_detail(db: Session, goods_id: int) -> Goods:
    goods = goods_repository.get_detail(db, goods_id)
    if goods is None:
        raise NotFoundError("존재하지 않는 상품입니다.")
    return goods


def register_goods(db: Session, seller: User, name: str, description: str, price: int, stock: int) -> Goods:
    name = name.strip()
    if not 1 <= len(name) <= 100:
        raise BusinessError("상품명은 1~100자로 입력해 주세요.")
    if price < 100:
        raise BusinessError("가격은 100원 이상이어야 합니다.")
    if stock < 0:
        raise BusinessError("재고는 0개 이상이어야 합니다.")

    goods = Goods(seller=seller, name=name, description=description.strip(), price=price, stock=stock)
    goods_repository.add(db, goods)
    db.commit()
    return goods


def delete_goods(db: Session, user: User, goods_id: int) -> str:
    """상품 삭제. 반환값: 삭제된 상품명.

    삭제 정책(수동 처리): 주문 이력이 있는 상품은 삭제할 수 없다.
    주문은 거래 기록이므로 보존해야 하기 때문이다. (models/goods.py 의 Goods.orders 주석 참고)
    """
    goods = goods_repository.get_by_id(db, goods_id)
    if goods is None:
        raise NotFoundError("존재하지 않는 상품입니다.")
    if goods.seller_id != user.id:
        raise PermissionDeniedError("본인이 등록한 상품만 삭제할 수 있습니다.")
    if goods_repository.has_orders(db, goods_id):
        raise BusinessError("주문 이력이 있는 상품은 삭제할 수 없습니다. (거래 기록 보존)")

    name = goods.name
    goods_repository.delete(db, goods)
    db.commit()
    return name
