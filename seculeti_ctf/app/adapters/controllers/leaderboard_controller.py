from __future__ import annotations

from flask import jsonify, render_template

from ...usecases.leaderboard import LeaderboardUseCase


def register_leaderboard_routes(app, leaderboard_uc: LeaderboardUseCase) -> None:
    @app.route("/leaderboard")
    def leaderboard():
        return render_template("leaderboard.html")

    @app.route("/api/leaderboard")
    def api_leaderboard():
        view = leaderboard_uc.execute()
        return jsonify(
            {
                "players": [
                    {
                        "username": p.username,
                        "score": p.score,
                        "solved": p.solved,
                        "last_solve": p.last_solve,
                    }
                    for p in view.players
                ],
                "total_tasks": view.total_tasks,
                "server_time": view.server_time,
            }
        )
