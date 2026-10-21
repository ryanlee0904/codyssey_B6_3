"""DB 엔진, 세션 팩토리, Declarative Base, 요청 단위 세션 의존성."""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    # SQLite는 기본적으로 생성한 스레드에서만 커넥션을 쓰도록 제한하므로 해제
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:
    # SQLite는 외래키 제약을 기본으로 검사하지 않는다.
    # ON DELETE RESTRICT / CASCADE 정책이 실제로 동작하도록 커넥션마다 켜준다.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """요청마다 DB 세션을 열고, 응답 후 닫는다. (FastAPI Depends 용)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
