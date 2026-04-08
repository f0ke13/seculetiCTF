from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

import bcrypt

from ..domain.entities import Proposal, Task
from ..domain.exceptions import DuplicateError, NotFoundError, ValidationError
from ..domain.repositories import (
    CategoryRepository,
    ProposalRepository,
    SolveRepository,
    TaskRepository,
    UserRepository,
    WriteupRepository,
)


@dataclass
class AdminDashboardView:
    user_count: int
    task_count: int
    pending_proposals: int


class AdminDashboardUseCase:
    def __init__(self, users: UserRepository, tasks: TaskRepository, proposals: ProposalRepository) -> None:
        self._users = users
        self._tasks = tasks
        self._proposals = proposals

    def execute(self) -> AdminDashboardView:
        return AdminDashboardView(
            user_count=self._users.count(),
            task_count=len(list(self._tasks.list_all())),
            pending_proposals=self._proposals.count_pending(),
        )


@dataclass
class AdminTasksView:
    tasks: List[Task]
    categories: list


class AdminTasksUseCase:
    def __init__(self, tasks: TaskRepository, categories: CategoryRepository) -> None:
        self._tasks = tasks
        self._categories = categories

    def execute(self) -> AdminTasksView:
        return AdminTasksView(
            tasks=list(self._tasks.list_all()),
            categories=list(self._categories.list_all()),
        )


class AdminAddTaskUseCase:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(
        self,
        title: str,
        category_id: int,
        description: str,
        points: int,
        flag: str,
    ) -> Task:
        if not title or not category_id or not description or not flag:
            raise ValidationError("Заполните все обязательные поля")
        if self._tasks.get_by_title(title):
            raise DuplicateError("Задача с таким названием уже существует")
        flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        task = Task(
            id=0,
            title=title,
            description=description,
            flag_hash=flag_hash,
            points=int(points) if str(points).isdigit() else 100,
            category_id=int(category_id),
        )
        return self._tasks.add(task)


class AdminEditTaskUseCase:
    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(
        self,
        task_id: int,
        title: str,
        category_id: int,
        description: str,
        points: int,
        flag: str | None = None,
    ) -> Task:
        task = self._tasks.get_by_id(task_id)
        if not task:
            raise NotFoundError("Задание не найдено")
        task.title = title or task.title
        task.category_id = int(category_id) if category_id else task.category_id
        task.description = description or task.description
        task.points = int(points) if str(points).isdigit() else task.points
        if flag:
            task.flag_hash = bcrypt.hashpw(flag.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self._tasks.update(task)
        return task


class AdminDeleteTaskUseCase:
    def __init__(
        self,
        tasks: TaskRepository,
        solves: SolveRepository,
        writeups: WriteupRepository,
    ) -> None:
        self._tasks = tasks
        self._solves = solves
        self._writeups = writeups

    def execute(self, task_id: int, confirm: str) -> None:
        if confirm != "yes":
            return
        if not self._tasks.get_by_id(task_id):
            raise NotFoundError("Задание не найдено")
        self._solves.delete_by_task(task_id)
        self._writeups.delete_by_task(task_id)
        self._tasks.delete(task_id)


@dataclass
class AdminProposalsView:
    proposals: List[Proposal]
    categories: list


class AdminProposalsUseCase:
    def __init__(self, proposals: ProposalRepository, categories: CategoryRepository) -> None:
        self._proposals = proposals
        self._categories = categories

    def execute(self) -> AdminProposalsView:
        return AdminProposalsView(
            proposals=list(self._proposals.list_pending()),
            categories=list(self._categories.list_all()),
        )


class AdminApproveProposalUseCase:
    def __init__(self, proposals: ProposalRepository, tasks: TaskRepository) -> None:
        self._proposals = proposals
        self._tasks = tasks

    def execute(
        self,
        proposal_id: int,
        title: str | None = None,
        description: str | None = None,
        points: int | None = None,
        flag: str | None = None,
    ) -> Task:
        proposal = self._proposals.get_by_id(proposal_id)
        if not proposal:
            raise NotFoundError("Предложение не найдено")
        proposal.title = title or proposal.title
        proposal.description = description or proposal.description
        proposal.points = int(points) if points is not None else proposal.points

        flag_value = flag or proposal.flag
        flag_hash = bcrypt.hashpw(flag_value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        task = Task(
            id=0,
            title=proposal.title,
            description=proposal.description,
            flag_hash=flag_hash,
            points=proposal.points,
            category_id=proposal.category_id,
        )
        self._tasks.add(task)
        proposal.status = "approved"
        self._proposals.update(proposal)
        return task


class AdminRejectProposalUseCase:
    def __init__(self, proposals: ProposalRepository) -> None:
        self._proposals = proposals

    def execute(self, proposal_id: int) -> Proposal:
        proposal = self._proposals.get_by_id(proposal_id)
        if not proposal:
            raise NotFoundError("Предложение не найдено")
        proposal.status = "rejected"
        self._proposals.update(proposal)
        return proposal
