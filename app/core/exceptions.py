"""도메인(비즈니스) 예외.

서비스 계층은 HTTP를 모른다. 규칙 위반은 이 예외로 표현하고,
라우터(화면 처리 계층)가 이를 받아 메시지/리다이렉트/에러 페이지로 바꾼다.
"""


class BusinessError(Exception):
    """비즈니스 규칙 위반 (예: 재고 부족, 허용되지 않는 상태 변경)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(BusinessError):
    """요청한 리소스가 없음 → 404 페이지."""


class PermissionDeniedError(BusinessError):
    """로그인은 했지만 해당 리소스의 소유자가 아님 → 403 페이지."""
