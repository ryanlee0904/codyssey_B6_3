# 🛒 Mini Shop — FastAPI 세션 인증 기반 미니 쇼핑몰

회원이 상품을 등록·주문하고, 주문 상태를 **주문접수 → 배송중 → 배송완료 / 주문취소** 로 변경하는 SSR 웹 서비스입니다.
FastAPI + SQLAlchemy ORM + Jinja2 템플릿으로 구현했습니다.

---

## 1. 개발 환경

| 항목 | 버전 |
|---|---|
| Python | **3.9 이상** (3.9.x 에서 개발·실행 확인, 3.10+ 에서도 동작) |
| fastapi | 0.115.6 |
| uvicorn | 0.34.0 |
| sqlalchemy | 2.0.36 |
| jinja2 | 3.1.5 |
| python-multipart | 0.0.20 |
| itsdangerous | 2.2.0 (세션 쿠키 서명) |
| bcrypt | 4.2.1 (비밀번호 해시) |
| starlette | fastapi 의존성으로 함께 설치 (SessionMiddleware) |
| DB | SQLite (`shop.db`, 서버 첫 실행 시 자동 생성) |

---

## 2. 실행 방법

### 터미널

```bash
# 1) 가상환경 생성
python -m venv venv

# 2) 가상환경 활성화
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

# 3) 패키지 설치
pip install -r requirements.txt

# 4) 서버 실행 (프로젝트 루트에서)
uvicorn app.main:app --reload
```

브라우저에서 <http://127.0.0.1:8080> 접속.
서버가 처음 뜰 때 테이블 생성과 테스트 데이터 입력이 자동으로 실행됩니다.

### PyCharm

1. `File > Open` 으로 프로젝트 폴더 열기
2. `Settings > Project > Python Interpreter > Add Interpreter > Virtualenv` 에서 Python 3.9+ 로 `venv` 생성
3. 터미널에서 `pip install -r requirements.txt`
4. `Run > Edit Configurations > + > Python` →
   - Module name: `uvicorn`
   - Script parameters: `app.main:app --reload`
   - Working directory: 프로젝트 루트
5. ▶ 실행

---

## 3. 테스트 계정

테스트 계정은 **DB 저장 방식**입니다. 서버 첫 실행 시 `app/seed.py` 가 bcrypt 로 해시한 비밀번호와 함께 DB에 넣습니다.

| ID | PW | 닉네임 | 용도 |
|---|---|---|---|
| `buyer1` | `buyer1234` | 김구매 | 구매자: 주문 → 주문 취소, 배송중 주문 수령 확인 (배송중 주문 1건 미리 생성됨) |
| `seller1` | `seller1234` | 이판매 | 판매자: 상품 4개 보유, 들어온 주문 배송 시작 |

`/signup` 에서 새 계정을 만들 수도 있습니다.

---

## 4. 인증 방식: 세션 기반 (방식 A)

로그인 성공 시 `starlette.middleware.sessions.SessionMiddleware` 의 서명된 쿠키에 `user_id` 만 저장하고,
이후 요청마다 `Depends(get_current_user_optional)` / `Depends(login_required)` 가 세션의 `user_id` 로 DB에서 회원을 조회합니다.

**선택 사유**
- **SSR(Jinja2) 화면 구조에 자연스럽다.** 브라우저가 쿠키를 자동으로 보내므로, JWT처럼 토큰을 JS로 저장하고 헤더에 실어 보내는 코드가 필요 없다.
- **로그아웃이 확실하다.** 세션을 비우면 즉시 로그아웃된다. JWT는 만료 전까지 토큰이 유효하므로 블랙리스트 같은 추가 장치가 필요하다.
- **로그인 후 안내 메시지(flash), 로그인 전 가려던 페이지(next) 같은 화면 흐름 상태를 세션에 함께 담기 쉽다.**
- 쿠키는 `itsdangerous` 로 서명되어 위변조가 불가하고, 쿠키에는 비밀번호·개인정보를 넣지 않는다.
- 비밀번호는 `bcrypt` 로 해시해 저장한다. (passlib 은 bcrypt 4.1+ 와 호환 문제가 있어 bcrypt 를 직접 사용)

---

## 5. 공개 / 보호 경로 정책

| 구분 | 경로 | 메서드 | 설명 | 비로그인 접근 시 |
|---|---|---|---|---|
| 공개 | `/` | GET | 홈 (최신 상품 미리보기, 로그인 상태별 UI) | 접근 가능 |
| 공개 | `/login` | GET, POST | 로그인 화면 / 로그인 처리 | 접근 가능 (로그인 상태면 상품 목록으로 이동) |
| 공개 | `/signup` | GET, POST | 회원가입 화면 / 처리 | 접근 가능 |
| 공개 | `/logout` | POST | 로그아웃 (세션 삭제) | 접근 가능 |
| 공개 | `/static/**` | GET | CSS | 접근 가능 |
| **보호** | `/app/goods/**` | GET, POST | 상품 목록·상세·등록·삭제 | `/login?next=원래경로` 로 이동 + "로그인이 필요한 페이지입니다" 안내 |
| **보호** | `/app/orders/**` | GET, POST | 주문 생성·목록·상세·상태 변경 | 〃 |
| **보호** | `/app/sales` | GET | 판매 관리 (내 상품에 들어온 주문) | 〃 |
| **보호** | `/app/me` | GET | 마이페이지 | 〃 |

- 보호 경로는 라우터 단위로 `APIRouter(dependencies=[Depends(login_required)])` 를 걸어 `/app/**` 전체를 막습니다.
- 로그인한 사용자라도 **본인과 관련 없는 주문**을 보거나, 남의 상품을 삭제하려 하면 403 화면을 보여줍니다. (역할 기반 권한은 없음, 소유자 확인만)
- 로그인 후에는 원래 가려던 페이지(`next`)로 돌아갑니다. 외부 URL 로의 이동(open redirect)은 차단합니다.

---

## 6. 주요 기능 경로

| 기능 | 메서드 | 경로 | 비고 |
|---|---|---|---|
| 홈 | GET | `/` | |
| 로그인 | GET / POST | `/login` | 실패 시 화면에 "로그인 실패" 메시지 + 401 |
| 회원가입 | GET / POST | `/signup` | |
| 로그아웃 | POST | `/logout` | |
| 상품 목록 | GET | `/app/goods` | 판매자(N:1) 함께 출력 |
| 상품 등록 | GET / POST | `/app/goods/new` | |
| 상품 상세 | GET | `/app/goods/{goods_id}` | 내 상품이면 이 상품의 주문 목록(1:N) 출력 |
| 상품 삭제 | POST | `/app/goods/{goods_id}/delete` | 주문 이력 있으면 거부 |
| 주문하기 | POST | `/app/orders` | 재고 차감, 상태 = 주문접수 |
| 내 주문 목록 | GET | `/app/orders?status_filter=ORDERED` | 상태별 필터 |
| 주문 상세 | GET | `/app/orders/{order_id}` | 상태 진행바 + 상태 이력 |
| **주문 취소** | POST | `/app/orders/{order_id}/cancel` | 구매자, 주문접수 → 주문취소 (재고 복구) |
| **배송 시작** | POST | `/app/orders/{order_id}/ship` | 판매자, 주문접수 → 배송중 |
| **수령 확인** | POST | `/app/orders/{order_id}/deliver` | 구매자, 배송중 → 배송완료 |
| 판매 관리 | GET | `/app/sales` | 내 상품에 들어온 주문 |
| 마이페이지 | GET | `/app/me` | `user.orders`, `user.goods` 연관 데이터 출력 |

---

## 7. 도메인 모델과 연관관계

```
User (user) 1 ──< N  Order (order_list)  N >── 1  Goods (goods)
   1                                                 N
   └────────────────────── 판매 ─────────────────────┘
```

| 관계 | 종류 | 방향 | 부모 삭제 시 정책 | 이유 |
|---|---|---|---|---|
| User → Order (`buyer`) | 1:N | 양방향 (`back_populates`) | `cascade="all, delete-orphan"` | 주문 내역은 구매자 개인 데이터. 탈퇴 시 함께 파기 |
| User → Goods (`seller`) | 1:N | 양방향 | cascade 없음, FK `RESTRICT` | 상품엔 남의 주문이 달려 있어 판매자 삭제로 지우면 안 됨 |
| Goods → Order (`goods`) | 1:N | 양방향 | cascade 없음, FK `RESTRICT` + 서비스에서 사전 검사 | 주문은 거래 기록이므로 보존. 주문 없는 상품만 삭제 가능 |

자세한 이유는 `app/models/*.py` 의 주석에 있습니다.

### 주문 상태 전이

```
주문접수(ORDERED) ──[판매자: 배송 시작]──▶ 배송중(SHIPPING) ──[구매자: 수령 확인]──▶ 배송완료(DELIVERED)
      │
      └──[구매자: 주문 취소, 재고 복구]──▶ 주문취소(CANCELLED)
```

허용되지 않는 변경(예: 배송중인 주문 취소)은 서비스 계층에서 거부되고 화면에 사유가 표시됩니다.
변경에 성공하면 `주문 #3 상태 변경: 주문접수 → 주문취소` 처럼 **변경 전/후**가 안내되고, 상세 화면의 진행바와 상태 이력이 바뀝니다.

---

## 8. 시연 흐름

1. `/app/orders` 접속 → 로그인 페이지로 이동 + 안내 메시지 확인
2. `buyer1 / buyer1234` 로그인 → "로그인 성공! 김구매님 환영합니다", 상단에 [로그아웃] 버튼
3. 상품 목록 → `무선 기계식 키보드` 상세 → 수량 2 주문 → 주문 상세(주문접수), 재고 10 → 8
4. [주문 취소] → "주문접수 → 주문취소" 안내, 재고 8 → 10 복구
5. 다시 주문 → 로그아웃 → `seller1` 로그인 → 판매 관리에서 [배송 시작]
6. 로그아웃 → `buyer1` 로그인 → 해당 주문 [수령 확인] → 배송완료
7. 마이페이지에서 주문/상품 목록과 상태별 건수 확인

---

## 9. 프로젝트 구조

```
mini-shop/
├── app/
│   ├── main.py              # 앱 생성, 미들웨어, 라우터 등록, 예외→화면 처리
│   ├── seed.py              # 테이블 생성 + 테스트 데이터
│   ├── auth/                # 인증·인가
│   │   ├── security.py      #   bcrypt 해시/검증
│   │   ├── session.py       #   세션 로그인/로그아웃, next 검증
│   │   └── dependencies.py  #   Depends: get_current_user_optional, login_required
│   ├── core/                # 설정, DB 연결, 템플릿, flash 메시지, 도메인 예외
│   ├── models/              # SQLAlchemy ORM (User, Goods, Order)
│   ├── repositories/        # 데이터 접근 (쿼리만, commit 없음)
│   ├── services/            # 비즈니스 로직 (검증, 상태 전이, 재고, commit)
│   ├── routers/             # 요청/응답 처리 (폼 → 서비스 호출 → 템플릿/리다이렉트)
│   ├── templates/           # Jinja2 SSR 템플릿
│   └── static/style.css
├── requirements.txt
└── README.md
```

계층 흐름: `routers → services → repositories → models`
라우터는 HTTP만, 서비스는 규칙만, 리포지토리는 쿼리만 담당합니다.
