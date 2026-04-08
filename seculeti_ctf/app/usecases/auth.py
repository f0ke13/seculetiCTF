from __future__ import annotations

import bcrypt

from ..domain.entities import User
from ..domain.exceptions import AuthError, DuplicateError, ValidationError
from ..domain.repositories import UserRepository


class RegisterUserUseCase:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, username: str, password: str) -> User:
        if not username or not password:
            raise ValidationError("Заполните все обязательные поля")
        if self._users.get_by_username(username):
            raise DuplicateError("Username already exists")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(id=0, username=username, password_hash=hashed, role="user")
        return self._users.add(user)


class LoginUserUseCase:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, username: str, password: str) -> User:
        if not username or not password:
            raise AuthError("Invalid credentials")
        user = self._users.get_by_username(username)
        if not user:
            raise AuthError("Invalid credentials")
        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise AuthError("Invalid credentials")
        return user
