"""테이블 생성 + 테스트 데이터 입력 (DB가 비어 있을 때 한 번만).

테스트 계정 (README 참고)
  - buyer1  / buyer1234   : 구매자 (주문 → 취소 / 수령확인 흐름 테스트용)
  - seller1 / seller1234  : 판매자 (상품 등록, 배송 시작 테스트용)
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.database import Base, SessionLocal, engine
from app.models import Goods, Order, OrderStatus, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(User.id).limit(1)) is None:
            _seed(db)


def _seed(db: Session) -> None:
    buyer = User(username="buyer1", nickname="김구매", password_hash=hash_password("buyer1234"))
    seller = User(username="seller1", nickname="이판매", password_hash=hash_password("seller1234"))

    keyboard = Goods(seller=seller, name="무선 기계식 키보드", price=89000, stock=10,
                     description="저소음 갈축, 블루투스 5.1 / 2.4GHz 겸용")
    mouse = Goods(seller=seller, name="버티컬 마우스", price=32000, stock=15,
                  description="손목 부담을 줄여주는 인체공학 마우스")
    monitor = Goods(seller=seller, name="27인치 QHD 모니터", price=289000, stock=3,
                    description="IPS 패널, 165Hz")
    hub = Goods(seller=seller, name="USB-C 7in1 허브", price=39000, stock=0,
                description="HDMI 4K, PD 100W 지원 (품절 예시 상품)")
    stand = Goods(seller=buyer, name="알루미늄 노트북 거치대", price=27000, stock=5,
                  description="buyer1 이 판매자로 등록한 상품 (seller1 로 주문 → buyer1 이 배송 시작 테스트)")

    # buyer1 이 바로 "수령 확인" 을 해볼 수 있도록 배송중 주문 1건을 미리 만들어 둔다.
    shipping_order = Order(buyer=buyer, goods=mouse, quantity=1, unit_price=mouse.price,
                           status=OrderStatus.SHIPPING, shipped_at=datetime.now())
    mouse.stock -= 1

    db.add_all([buyer, seller, keyboard, mouse, monitor, hub, stand, shipping_order])
    db.commit()
