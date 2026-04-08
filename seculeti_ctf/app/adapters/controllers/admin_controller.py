from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for

from ...domain.exceptions import DuplicateError, NotFoundError, ValidationError
from ...usecases.admin import (
    AdminAddTaskUseCase,
    AdminApproveProposalUseCase,
    AdminDashboardUseCase,
    AdminDeleteTaskUseCase,
    AdminEditTaskUseCase,
    AdminProposalsUseCase,
    AdminRejectProposalUseCase,
    AdminTasksUseCase,
)
from ...domain.repositories import UserRepository
from .common import admin_required


def register_admin_routes(
    app,
    users_repo: UserRepository,
    dashboard_uc: AdminDashboardUseCase,
    tasks_uc: AdminTasksUseCase,
    add_task_uc: AdminAddTaskUseCase,
    edit_task_uc: AdminEditTaskUseCase,
    delete_task_uc: AdminDeleteTaskUseCase,
    proposals_uc: AdminProposalsUseCase,
    approve_uc: AdminApproveProposalUseCase,
    reject_uc: AdminRejectProposalUseCase,
) -> None:
    admin_guard = admin_required(users_repo)

    @app.route("/admin")
    @admin_guard
    def admin_dashboard():
        view = dashboard_uc.execute()
        return render_template(
            "admin.html",
            user_count=view.user_count,
            task_count=view.task_count,
            pending_proposals=view.pending_proposals,
        )

    @app.route("/admin/tasks")
    @admin_guard
    def admin_tasks():
        view = tasks_uc.execute()
        return render_template("admin_tasks.html", tasks=view.tasks, categories=view.categories)

    @app.route("/admin/tasks/add", methods=["POST"])
    @admin_guard
    def admin_tasks_add():
        title = request.form.get("title")
        category_id = request.form.get("category_id")
        description = request.form.get("description")
        points = request.form.get("points", 100)
        flag = request.form.get("flag")

        try:
            add_task_uc.execute(
                title=title or "",
                category_id=int(category_id) if category_id else 0,
                description=description or "",
                points=int(points) if str(points).isdigit() else 100,
                flag=flag or "",
            )
        except ValidationError:
            flash("Заполните все обязательные поля", "error")
            return redirect(url_for("admin_tasks"))
        except DuplicateError:
            flash("Задача с таким названием уже существует", "error")
            return redirect(url_for("admin_tasks"))

        flash("Задача добавлена", "success")
        return redirect(url_for("admin_tasks"))

    @app.route("/admin/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    @admin_guard
    def admin_tasks_edit(task_id: int):
        if request.method == "GET":
            view = tasks_uc.execute()
            task = next((t for t in view.tasks if t.id == task_id), None)
            if not task:
                abort(404)
            return render_template("edit_task.html", task=task, categories=view.categories)

        category_raw = request.form.get("category_id")
        points_raw = request.form.get("points")
        try:
            edit_task_uc.execute(
                task_id=task_id,
                title=request.form.get("title") or "",
                category_id=int(category_raw) if category_raw else 0,
                description=request.form.get("description") or "",
                points=int(points_raw) if points_raw and str(points_raw).isdigit() else 0,
                flag=request.form.get("flag") or None,
            )
        except NotFoundError:
            abort(404)

        flash("Задача обновлена", "success")
        return redirect(url_for("admin_tasks"))

    @app.route("/admin/tasks/<int:task_id>/delete", methods=["POST"])
    @admin_guard
    def admin_tasks_delete(task_id: int):
        try:
            delete_task_uc.execute(task_id=task_id, confirm=request.form.get("confirm", ""))
        except NotFoundError:
            abort(404)
        flash("Задача удалена", "success")
        return redirect(url_for("admin_tasks"))

    @app.route("/admin/proposals", methods=["GET"])
    @admin_guard
    def admin_proposals():
        view = proposals_uc.execute()
        return render_template("admin_proposals.html", proposals=view.proposals, categories=view.categories)

    @app.route("/admin/suggest/<int:prop_id>/approve", methods=["POST"])
    @admin_guard
    def admin_suggest_approve(prop_id: int):
        points_raw = request.form.get("points")
        try:
            approve_uc.execute(
                proposal_id=prop_id,
                title=request.form.get("title") or None,
                description=request.form.get("description") or None,
                points=int(points_raw) if points_raw and str(points_raw).isdigit() else None,
                flag=request.form.get("flag") or None,
            )
        except NotFoundError:
            abort(404)
        flash("Предложение одобрено и добавлено", "success")
        return redirect(url_for("admin_proposals"))

    @app.route("/admin/suggest/<int:prop_id>/reject", methods=["POST"])
    @admin_guard
    def admin_suggest_reject(prop_id: int):
        try:
            reject_uc.execute(proposal_id=prop_id)
        except NotFoundError:
            abort(404)
        flash("Предложение отклонено", "success")
        return redirect(url_for("admin_proposals"))