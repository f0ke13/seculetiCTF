from __future__ import annotations

import os

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader

from ..adapters.controllers.admin_controller import register_admin_routes
from ..adapters.controllers.auth_controller import register_auth_routes
from ..adapters.controllers.leaderboard_controller import register_leaderboard_routes
from ..adapters.controllers.suggestions_controller import register_suggestion_routes
from ..adapters.controllers.tasks_controller import register_task_routes
from ..adapters.controllers.writeups_controller import register_writeup_routes
from .config import Config
from .di import build_container


def create_app() -> Flask:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    templates_dir = os.path.join(base_dir, "templates")
    legacy_templates_dir = os.path.abspath(os.path.join(base_dir, "..", "front_end-demo"))
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.config.from_object(Config)
    if os.path.isdir(legacy_templates_dir):
        app.jinja_loader = ChoiceLoader(
            [
                FileSystemLoader(templates_dir),
                FileSystemLoader(legacy_templates_dir),
            ]
        )

    container = build_container()

    register_auth_routes(app, container.login_uc, container.register_uc)
    register_task_routes(
        app,
        container.category_uc,
        container.task_detail_uc,
        container.category_tasks_uc,
        container.titles_uc,
        container.submit_flag_uc,
        container.forfeit_uc,
    )
    register_leaderboard_routes(app, container.leaderboard_uc)
    register_suggestion_routes(app, container.list_suggestions_uc, container.submit_suggestion_uc)
    register_admin_routes(
        app,
        container.users,
        container.admin_dashboard_uc,
        container.admin_tasks_uc,
        container.admin_add_task_uc,
        container.admin_edit_task_uc,
        container.admin_delete_task_uc,
        container.admin_proposals_uc,
        container.admin_approve_uc,
        container.admin_reject_uc,
    )
    register_writeup_routes(app, container.list_writeups_uc, container.submit_writeup_uc)

    return app