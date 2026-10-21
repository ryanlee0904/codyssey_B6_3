"""비밀번호 해시/검증.

passlib 대신 bcrypt 를 직접 사용한다.
(passlib 1.7.4는 더 이상 관리되지 않고, bcrypt 4.1+ 와 함께 쓰면 버전 탐지 오류가 난다.)
"""
import bcrypt

# bcrypt는 72바이트까지만 비밀번호로 사용한다. 그 이상은 회원가입 단계에서 막는다.
BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # 72바이트 초과 입력 또는 손상된 해시 → 로그인 실패로 처리
        return False
