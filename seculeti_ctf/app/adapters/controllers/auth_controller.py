from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for

from ...domain.exceptions import AuthError, DuplicateError, ValidationError
from ...usecases.auth import LoginUserUseCase, RegisterUserUseCase


def register_auth_routes(app, login_uc: LoginUserUseCase, register_uc: RegisterUserUseCase) -> None:
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("category"))
        return render_template("main.html")

    @app.route("/about", methods=["GET"])
    def about():
        return render_template("about.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            user = login_uc.execute(username=username, password=password)
        except AuthError:
            flash("Invalid credentials", "error")
            return render_template("login.html")
        session["user_id"] = user.id
        session["username"] = user.username
        return redirect(url_for("category"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("register.html")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            register_uc.execute(username=username, password=password)
        except DuplicateError:
            flash("Username already exists", "error")
            return render_template("register.html")
        except ValidationError:
            flash("Заполните все обязательные поля", "error")
            return render_template("register.html")
        flash("Registration successful", "success")
        return redirect(url_for("login"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out successfully", "success")
        return redirect(url_for("login"))
