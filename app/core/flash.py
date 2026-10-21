"""한 번만 보여주는 안내 메시지(flash).

리다이렉트 이후 화면에서 "로그인 성공", "주문 취소됨" 같은 결과를 보여주기 위해
세션에 잠깐 저장했다가 다음 렌더링 때 꺼내서 지운다.
category: success | error | warning | info
"""
from fastapi import Request

_FLASH_KEY = "_flashes"


def flash(request: Request, message: str, category: str = "info") -> None:
    flashes = list(request.session.get(_FLASH_KEY, []))
    flashes.append({"message": message, "category": category})
    request.session[_FLASH_KEY] = flashes


def pop_flashes(request: Request) -> list[dict]:
    return request.session.pop(_FLASH_KEY, [])
