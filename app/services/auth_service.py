"""회원가입 / 로그인 검증 비즈니스 로직."""
from typing import Optional
import re

from sqlalchemy.orm import Session

from app.auth.security import BCRYPT_MAX_BYTES, hash_password, verify_password
from app.core.exceptions import BusinessError
from app.models import User
from app.repositories import user_repository

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{4,20}$")


def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    """ID/PW가 맞으면 User, 틀리면 None.

    ID가 없는 경우와 비밀번호가 틀린 경우를 구분하지 않는다.
    (어떤 ID가 존재하는지 외부에 알려주지 않기 위해)
    """
    user = user_repository.get_by_username(db, username.strip())
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def signup(db: Session, username: str, nickname: str, password: str, password_confirm: str) -> User:
    username, nickname = username.strip(), nickname.strip()

    if not _USERNAME_RE.match(username):
        raise BusinessError("아이디는 영문/숫자/밑줄(_) 4~20자로 입력해 주세요.")
    if not 1 <= len(nickname) <= 20:
        raise BusinessError("닉네임은 1~20자로 입력해 주세요.")
    if len(password) < 8:
        raise BusinessError("비밀번호는 8자 이상이어야 합니다.")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise BusinessError("비밀번호가 너무 깁니다.")
    if password != password_confirm:
        raise BusinessError("비밀번호 확인이 일치하지 않습니다.")
    if user_repository.get_by_username(db, username):
        raise BusinessError("이미 사용 중인 아이디입니다.")

    user = User(username=username, nickname=nickname, password_hash=hash_password(password))
    user_repository.add(db, user)
    db.commit()
    return user
