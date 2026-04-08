from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from ..domain.repositories import SolveRepository, TaskRepository, UserRepository

MSK = timezone(timedelta(hours=3))


@dataclass
class LeaderboardEntry:
    username: str
    score: int
    solved: int
    last_solve: str


@dataclass
class LeaderboardView:
    players: List[LeaderboardEntry]
    total_tasks: int
    server_time: str


class LeaderboardUseCase:
    def __init__(self, users: UserRepository, tasks: TaskRepository, solves: SolveRepository) -> None:
        self._users = users
        self._tasks = tasks
        self._solves = solves

    def execute(self) -> LeaderboardView:
        total_tasks = len(list(self._tasks.list_all()))
        user_map = {u.id: u.username for u in self._users.list_all()}

        score_map = {}
        solved_map = {}
        last_solve_map = {}

        for solve in self._solves.list_all():
            if solve.is_forfeit:
                continue
            score_map[solve.user_id] = score_map.get(solve.user_id, 0) + solve.points_awarded
            solved_map[solve.user_id] = solved_map.get(solve.user_id, 0) + 1
            last = last_solve_map.get(solve.user_id)
            if last is None or solve.solved_at > last:
                last_solve_map[solve.user_id] = solve.solved_at

        entries_with_id = []
        for user_id, score in score_map.items():
            last_dt = last_solve_map.get(user_id)
            last_msk = "-"
            if last_dt:
                utc_dt = last_dt.replace(tzinfo=timezone.utc)
                last_msk = utc_dt.astimezone(MSK).strftime("%H:%M")
            entries_with_id.append(
                (
                    user_id,
                    LeaderboardEntry(
                        username=user_map.get(user_id, "Unknown"),
                        score=int(score),
                        solved=int(solved_map.get(user_id, 0)),
                        last_solve=last_msk,
                    ),
                )
            )

        entries_with_id.sort(
            key=lambda item: (
                -item[1].score,
                last_solve_map.get(item[0], datetime.max),
            )
        )
        entries: List[LeaderboardEntry] = [entry for _, entry in entries_with_id]
        now_msk = datetime.now(MSK)
        return LeaderboardView(
            players=entries,
            total_tasks=total_tasks,
            server_time=now_msk.strftime("%d %b %Y %H:%M:%S MSK"),
        )