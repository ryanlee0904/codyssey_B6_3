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

브라우저에서 <http://127.0.0.1:8000> 접속.

> **Windows 에서 `[WinError 10013] 액세스 권한에 의해 숨겨진 소켓에 액세스를 시도했습니다` 가 나오면**
> 8000번 포트가 다른 프로그램에 사용 중이거나 Windows(Hyper-V/WSL)에 예약된 경우입니다.
> 포트를 바꿔 실행하세요: `uvicorn app.main:app --reload --port 8080` → <http://127.0.0.1:8080>

서버가 처음 뜰 때 테이블 생성과 테스트 데이터 입력이 자동으로 실행됩니다.
데이터를 초기화하려면 서버를 끄고 `shop.db` 파일을 삭제한 뒤 다시 실행하세요.

### PyCharm

1. `File > Open` 으로 프로젝트 폴더 열기
2. `Settings > Project > Python Interpreter > Add Interpreter > Virtualenv` 에서 Python 3.9+ 로 `venv` 생성
3. 터미널에서 `pip install -r requirements.txt`
4. `Run > Edit Configurations > + > Python` →
   - Module name: `uvicorn`
   - Script parameters: `app.main:app --reload` (포트 충돌 시 `--port 8080` 추가)
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
├── docs/QA.md               # 예상 질문과 답변
├── requirements.txt
└── README.md
```

계층 흐름: `routers → services → repositories → models`
라우터는 HTTP만, 서비스는 규칙만, 리포지토리는 쿼리만 담당합니다.

---

## 10. 설계 설명

> 발표·리뷰용 예상 질문과 답변은 [`docs/QA.md`](docs/QA.md) 에 정리했습니다.

### 10-1. Depends 기반 인증/인가 흐름

```
로그인:  POST /login
  → auth_service.authenticate()  : username 조회 + bcrypt.checkpw()
  → auth/session.login_user()    : session.clear() 후 session["user_id"] = user.id
  → SessionMiddleware            : itsdangerous 로 서명한 쿠키를 응답에 실음

이후 요청:
  get_db                       요청 단위 DB 세션
   └ get_current_user_optional  세션의 user_id → DB 에서 User 조회 (없으면 None)
                                결과를 request.state.user 에도 저장 → 템플릿 UI 분기
      └ login_required          None 이면 LoginRequiredException, 있으면 User 반환

로그아웃: POST /logout → session.clear() → 다음 요청부터 즉시 비로그인
```

- 핸들러는 `user: User = Depends(login_required)` 만 선언하면 로그인된 사용자 객체를 받습니다.
- 같은 요청 안에서 의존성 결과는 캐시되므로, 라우터와 핸들러에 동시에 선언해도 조회는 한 번입니다.
- 인증 로직은 `app/auth/` 에만 있고, 핸들러는 세션을 직접 다루지 않습니다.

### 10-2. 비로그인 요청이 차단되는 위치와 이유

| 단계 | 위치 | 역할 |
|---|---|---|
| ① 판정 | `auth/dependencies.py` `login_required` | 사용자가 없으면 `LoginRequiredException(next_url)` 발생 |
| ② 적용 범위 | `routers/goods.py`, `orders.py`, `mypage.py` | `APIRouter(dependencies=[Depends(login_required)])` → `/app/**` 전체 보호 |
| ③ 응답 변환 | `main.py` `exception_handler(LoginRequiredException)` | 안내 메시지(flash) + `303 → /login?next=원래경로` |

- FastAPI 는 **핸들러 호출 전에 의존성을 먼저 실행**하므로, 예외가 나면 핸들러 본문은 실행되지 않습니다.
- 라우터 단위로 걸었기 때문에 새 기능을 추가할 때 인증 체크를 빠뜨릴 수 없습니다.
- 차단 이유: 주문·판매·마이페이지는 "누구의 데이터인가"가 필수인 기능입니다.
- **인증(로그인 여부)** 과 **소유권(본인 데이터인가)** 은 분리했습니다. 로그인했어도 남의 주문 접근 시 서비스가 `PermissionDeniedError` → 403.

### 10-3. 연관관계를 객체 관점에서, 그리고 매핑 이유

- 코드에서 외래키 숫자 대신 객체를 따라갑니다: `order.goods.seller.nickname`, `user.orders`, `goods.orders`.
- `back_populates` 로 양방향을 맞춰, `Order(buyer=user, goods=goods)` 만 만들면 `user.orders`·`goods.orders` 에도 반영되고 FK 는 SQLAlchemy 가 채웁니다.
- **Order 를 독립 모델로 둔 이유:** User–Goods 는 본질적으로 N:M 이지만 그 사이에 수량, 주문 시점 단가(`unit_price`), 상태, 처리 시각이라는 고유 데이터가 있으므로 연결 테이블이 아닌 중간 모델로 풀었습니다.
- **`unit_price` 스냅샷:** 상품 가격이 바뀌어도 과거 주문 금액은 변하지 않아야 합니다.
- **삭제 정책** 은 7장 표 참고. 주문(거래 기록)은 보존을 우선해 `RESTRICT`, 구매자 개인 데이터는 탈퇴 시 `delete-orphan` 으로 함께 파기.
  `passive_deletes="all"` 로 SQLAlchemy 가 FK 를 임의로 NULL 처리하지 않고 DB 제약에 맡기며, SQLite 는 `PRAGMA foreign_keys=ON` 으로 제약을 켭니다.
- 리포지토리에서 `joinedload` / `selectinload` 로 관계를 미리 로딩해 템플릿에서 N+1 쿼리가 생기지 않게 했습니다.

### 10-4. 상태 변경 로직이 중요한 이유와 위치

단순 `UPDATE status=?` 로 처리하면 ① 배송완료 → 주문접수 같은 잘못된 전이, ② 취소했는데 재고 미복구 같은 데이터 불일치, ③ 구매자가 "배송 시작"을 누르는 권한 문제가 생깁니다.
상태 변경은 **규칙(허용 전이) + 권한(누가) + 부수효과(재고·시각 기록)** 가 함께 움직이는 비즈니스 행위이므로 한곳에서 다룹니다.

| 계층 | 파일 | 역할 |
|---|---|---|
| 모델 | `models/order.py` | `OrderStatus`, `ALLOWED_TRANSITIONS` 전이 표, `can_change_to()` |
| 서비스 | `services/order_service.py` | 권한 확인 → `_transition()` 전이 검증 → 재고 복구/시각 기록 → `commit` 1회 |
| 라우터 | `routers/orders.py` | 결과를 "주문접수 → 주문취소" 메시지로, 실패는 사유 메시지로 변환 |
| 템플릿 | `templates/orders/detail.html` | 상태·역할에 맞는 버튼만 노출, 진행바·상태 이력 표시 |

- 화면에서 버튼을 숨겨도 POST 를 직접 보낼 수 있으므로 **최종 판단은 서비스**가 합니다.
- `_transition()` 이 `StatusChange(before, after)` 를 반환해 변경 전/후가 화면에 명확히 드러납니다.
- 상태 변경과 재고 복구가 같은 `commit` 으로 묶여 원자적으로 처리됩니다.

### 10-5. 전체 구조: 사용자 관점 / 개발자 관점

**사용자 관점:** 홈 → 로그인 → 상품 목록·상세 → 주문(주문접수) → 주문 취소 / 배송 시작 / 수령 확인 → 진행바·이력·마이페이지에서 결과 확인.

**개발자 관점 (`POST /app/orders/3/cancel` 한 건의 흐름):**

```
브라우저(세션 쿠키)
 → SessionMiddleware              쿠키 검증 → request.session
 → 라우터 의존성 (auth/)            get_db → get_current_user_optional → login_required
 → routers/orders.py              파라미터 수신, 서비스 호출, 도메인 예외 → flash/화면
 → services/order_service.py      권한 확인, 전이 검증, 재고 복구, commit
 → repositories/order_repository  쿼리 + 관계 로딩
 → models/ → SQLite
 ← 303 → GET /app/orders/3 → Jinja2 렌더(변경 결과 표시)
```

서비스는 HTTP 를 모르고 `BusinessError` / `NotFoundError` / `PermissionDeniedError` 만 던지며, 이를 화면으로 바꾸는 일은 라우터와 `main.py` 가 담당합니다.
그래서 규칙 변경은 서비스만, 화면 변경은 템플릿만 수정하면 됩니다.
