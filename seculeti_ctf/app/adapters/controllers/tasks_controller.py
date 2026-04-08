from __future__ import annotations

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from ...domain.exceptions import NotFoundError
from ...usecases.submissions import ForfeitTaskUseCase, SubmitFlagUseCase
from ...usecases.tasks import CategoryOverviewUseCase, CategoryTasksUseCase, TaskDetailUseCase, TasksByTitleUseCase
from .common import login_required


def register_task_routes(
    app,
    category_uc: CategoryOverviewUseCase,
    task_detail_uc: TaskDetailUseCase,
    category_tasks_uc: CategoryTasksUseCase,
    titles_uc: TasksByTitleUseCase,
    submit_flag_uc: SubmitFlagUseCase,
    forfeit_uc: ForfeitTaskUseCase,
) -> None:
    @app.route("/category", methods=["GET"])
    @login_required
    def category():
        overview = category_uc.execute(user_id=session["user_id"])
        return render_template(
            "category.html",
            categories=overview.categories,
            tasks=overview.tasks,
            solved_tasks=overview.solved_task_ids,
        )

    @app.route("/submit_flag", methods=["POST"])
    @login_required
    def submit_flag():
        data = request.get_json(silent=True) or {}
        flag = request.form.get("flag") or data.get("flag") or ""
        result = submit_flag_uc.execute(user_id=session["user_id"], flag=flag)
        return jsonify(
            {
                "success": result.success,
                "message": result.message,
                "points": result.points,
                "task": result.task_title,
            }
        )

    @app.route("/<category_name>/<task_name>")
    @login_required
    def task_detail(category_name: str, task_name: str):
        try:
            detail = task_detail_uc.execute(
                user_id=session["user_id"],
                category_name=category_name,
                task_name=task_name,
            )
        except NotFoundError as exc:
            flash(str(exc), "error")
            return redirect(url_for("category"))
        return render_template(
            "task.html",
            task=detail.task,
            category=detail.category,
            solved=detail.solved,
            forfeit=detail.forfeit,
        )

    @app.route("/osint")
    @login_required
    def osint():
        try:
            view = category_tasks_uc.execute(user_id=session["user_id"], category_name="OSINT")
        except NotFoundError as exc:
            flash(str(exc), "error")
            return redirect(url_for("category"))
        return render_template(
            "osint.html",
            category=view.category,
            tasks=view.tasks,
            solved_tasks=view.solved_task_ids,
        )

    @app.route("/beginner")
    @login_required
    def beginner():
        try:
            view = category_tasks_uc.execute(user_id=session["user_id"], category_name="Beginner")
        except NotFoundError as exc:
            flash(str(exc), "error")
            return redirect(url_for("category"))
        return render_template(
            "begginer.html",
            category=view.category,
            tasks=view.tasks,
            solved_tasks=view.solved_task_ids,
        )

    @app.route("/tasks/<int:task_id>/forfeit", methods=["POST"])
    @login_required
    def forfeit_task(task_id: int):
        result = forfeit_uc.execute(user_id=session["user_id"], task_id=task_id)
        category_redirect = request.referrer or url_for("category")
        if result.status == "created":
            flash(result.message, "success")
            return redirect(url_for("writeups", task_id=task_id))
        if result.status == "already_forfeit":
            flash(result.message, "error")
            return redirect(category_redirect)
        if result.status == "already_solved":
            flash(result.message, "success")
            return redirect(category_redirect)
        flash(result.message, "error")
        return redirect(category_redirect)