from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from ..domain.entities import Task, Writeup
from ..domain.exceptions import DuplicateError, ValidationError
from ..domain.repositories import SolveRepository, TaskRepository, UserRepository, WriteupRepository


@dataclass
class WriteupView:
    writeups: List[Tuple[Writeup, str, str]]
    tasks: List[Task]
    current_task_id: Optional[int]


class ListWriteupsUseCase:
    def __init__(
        self,
        writeups: WriteupRepository,
        tasks: TaskRepository,
        users: UserRepository,
        solves: SolveRepository,
    ) -> None:
        self._writeups = writeups
        self._tasks = tasks
        self._users = users
        self._solves = solves

    def execute(self, user_id: int, task_id: Optional[int]) -> WriteupView:
        allowed_solves = list(self._solves.list_by_user(user_id))
        allowed_task_ids = {s.task_id for s in allowed_solves}

        if task_id and task_id not in allowed_task_ids:
            raise ValidationError("Для доступа к райтапам решите задачу или выберите просмотр с 0 баллов.")

        if task_id:
            ws = list(self._writeups.list_by_task_id(task_id))
        else:
            ws = list(self._writeups.list_by_task_ids(allowed_task_ids))

        tasks = list(self._tasks.list_all())
        writeups_formatted = []
        for w in ws:
            user = self._users.get_by_id(w.user_id)
            task = self._tasks.get_by_id(w.task_id)
            writeups_formatted.append((w, user.username if user else "Unknown", task.title if task else "Unknown"))

        return WriteupView(writeups=writeups_formatted, tasks=tasks, current_task_id=task_id)


class SubmitWriteupUseCase:
    def __init__(
        self,
        writeups: WriteupRepository,
        solves: SolveRepository,
    ) -> None:
        self._writeups = writeups
        self._solves = solves

    def execute(self, user_id: int, task_id: int, content: str) -> Writeup:
        if not task_id or not content:
            raise ValidationError("Заполните все поля")
        solve = self._solves.get_by_user_task(user_id, task_id)
        if not solve or solve.is_forfeit:
            raise ValidationError("Нельзя опубликовать райтап для нерешённого задания")
        if self._writeups.get_by_user_task(user_id, task_id):
            raise DuplicateError("Вы уже добавили райтап для этого задания")
        writeup = Writeup(
            id=0,
            user_id=user_id,
            task_id=task_id,
            content=content,
            created_at=datetime.utcnow(),
        )
        return self._writeups.add(writeup)
