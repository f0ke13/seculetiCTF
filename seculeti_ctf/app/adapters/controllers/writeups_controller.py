from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for

from ...domain.exceptions import DuplicateError, ValidationError
from ...usecases.writeups import ListWriteupsUseCase, SubmitWriteupUseCase
from .common import login_required


def register_writeup_routes(
    app,
    list_uc: ListWriteupsUseCase,
    submit_uc: SubmitWriteupUseCase,
) -> None:
    @app.route("/writeups", methods=["GET"])
    @login_required
    def writeups():
        task_id = request.args.get("task_id", type=int)
        try:
            view = list_uc.execute(user_id=session["user_id"], task_id=task_id)
        except ValidationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("category"))
        return render_template(
            "writeups.html",
            writeups=view.writeups,
            tasks=view.tasks,
            current_task_id=view.current_task_id,
        )

    @app.route("/writeups/submit", methods=["POST"])
    @login_required
    def writeups_submit():
        task_id = request.form.get("task_id")
        content = request.form.get("content")
        try:
            submit_uc.execute(
                user_id=session["user_id"],
                task_id=int(task_id) if task_id else 0,
                content=content or "",
            )
        except ValidationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("writeups"))
        except DuplicateError as exc:
            flash(str(exc), "error")
            return redirect(url_for("writeups"))

        flash("Райтап добавлен", "success")
        return redirect(url_for("writeups"))
