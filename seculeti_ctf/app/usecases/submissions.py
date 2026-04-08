from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import bcrypt

from ..domain.entities import Solve
from ..domain.repositories import SolveRepository, TaskRepository


@dataclass
class SubmitFlagResult:
    success: bool
    message: str
    points: int = 0
    task_title: str = ""


class SubmitFlagUseCase:
    def __init__(self, tasks: TaskRepository, solves: SolveRepository) -> None:
        self._tasks = tasks
        self._solves = solves

    def execute(self, user_id: int, flag: str) -> SubmitFlagResult:
        flag_bytes = flag.encode("utf-8")
        for task in self._tasks.list_all():
            if bcrypt.checkpw(flag_bytes, task.flag_hash.encode("utf-8")):
                existing = self._solves.get_by_user_task(user_id, task.id)
                if not existing:
                    solve = Solve(
                        id=0,
                        user_id=user_id,
                        task_id=task.id,
                        solved_at=datetime.utcnow(),
                        points_awarded=task.points,
                        is_forfeit=False,
                    )
                    self._solves.add(solve)
                    return SubmitFlagResult(
                        success=True,
                        message=f"Correct flag! +{task.points} баллов.",
                        points=task.points,
                        task_title=task.title,
                    )
                if existing.is_forfeit:
                    existing.points_awarded = task.points
                    existing.is_forfeit = False
                    existing.solved_at = datetime.utcnow()
                    self._solves.update(existing)
                    return SubmitFlagResult(
                        success=True,
                        message=f"Correct flag! +{task.points} баллов.",
                        points=task.points,
                        task_title=task.title,
                    )
                return SubmitFlagResult(success=False, message="Уже решено")
        return SubmitFlagResult(success=False, message="Неверный флаг")


@dataclass
class ForfeitResult:
    status: str
    message: str


class ForfeitTaskUseCase:
    def __init__(self, tasks: TaskRepository, solves: SolveRepository) -> None:
        self._tasks = tasks
        self._solves = solves

    def execute(self, user_id: int, task_id: int) -> ForfeitResult:
        task = self._tasks.get_by_id(task_id)
        if not task:
            return ForfeitResult(status="not_found", message="Задание не найдено")
        existing = self._solves.get_by_user_task(user_id, task_id)
        if existing:
            if existing.is_forfeit:
                return ForfeitResult(
                    status="already_forfeit",
                    message="Вы уже выбрали просмотр райтапов с 0 баллов.",
                )
            return ForfeitResult(
                status="already_solved",
                message="Задача уже решена. Райтапы доступны.",
            )
        solve = Solve(
            id=0,
            user_id=user_id,
            task_id=task_id,
            solved_at=datetime.utcnow(),
            points_awarded=0,
            is_forfeit=True,
        )
        self._solves.add(solve)
        return ForfeitResult(
            status="created",
            message="Задача отмечена как нерешённая. Райтапы доступны (0 баллов).",
        )
