from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for

from ...domain.exceptions import DuplicateError, ValidationError
from ...usecases.suggestions import ListSuggestionsUseCase, SubmitSuggestionUseCase
from .common import login_required


def register_suggestion_routes(
    app,
    list_uc: ListSuggestionsUseCase,
    submit_uc: SubmitSuggestionUseCase,
) -> None:
    @app.route("/suggest", methods=["GET"])
    @login_required
    def suggest():
        view = list_uc.execute(user_id=session["user_id"])
        return render_template("proposals.html", proposals=view.proposals, categories=view.categories)

    @app.route("/suggest/submit", methods=["POST"])
    @login_required
    def suggest_submit():
        title = request.form.get("title")
        category_id = request.form.get("category_id")
        description = request.form.get("description")
        points = request.form.get("points", 100)
        flag = request.form.get("flag")
        hints = request.form.get("hints", "")
        difficulty = request.form.get("difficulty", "medium")

        try:
            submit_uc.execute(
                user_id=session["user_id"],
                title=title or "",
                category_id=int(category_id) if category_id else 0,
                description=description or "",
                points=int(points) if str(points).isdigit() else 100,
                flag=flag or "",
                hints=hints or "",
                difficulty=difficulty or "medium",
            )
        except ValidationError:
            flash("Заполните все обязательные поля", "error")
            return redirect(url_for("suggest"))
        except DuplicateError:
            flash("Задача с таким названием уже существует", "error")
            return redirect(url_for("suggest"))

        flash("Отправлено на проверку", "success")
        return redirect(url_for("suggest"))
