from __future__ import annotations

from functools import wraps

from flask import flash, redirect, session, url_for

from ...domain.repositories import UserRepository


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def admin_required(users: UserRepository):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            user = users.get_by_id(session["user_id"])
            if not user or user.role != "admin":
                flash("Доступ запрещен", "error")
                return redirect(url_for("category"))
            return func(*args, **kwargs)

        return wrapper

    return decorator
