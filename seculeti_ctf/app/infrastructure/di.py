from __future__ import annotations

from dataclasses import dataclass

import bcrypt

from ..adapters.repositories.in_memory import (
    InMemoryCategoryRepository,
    InMemoryProposalRepository,
    InMemorySolveRepository,
    InMemoryTaskRepository,
    InMemoryUserRepository,
    InMemoryWriteupRepository,
)
from ..domain.entities import Category, Task, User
from ..usecases.admin import (
    AdminAddTaskUseCase,
    AdminApproveProposalUseCase,
    AdminDashboardUseCase,
    AdminDeleteTaskUseCase,
    AdminEditTaskUseCase,
    AdminProposalsUseCase,
    AdminRejectProposalUseCase,
    AdminTasksUseCase,
)
from ..usecases.auth import LoginUserUseCase, RegisterUserUseCase
from ..usecases.leaderboard import LeaderboardUseCase
from ..usecases.submissions import ForfeitTaskUseCase, SubmitFlagUseCase
from ..usecases.suggestions import ListSuggestionsUseCase, SubmitSuggestionUseCase
from ..usecases.tasks import CategoryOverviewUseCase, CategoryTasksUseCase, TaskDetailUseCase, TasksByTitleUseCase
from ..usecases.writeups import ListWriteupsUseCase, SubmitWriteupUseCase
from .db import InMemoryDB, create_db


@dataclass
class Container:
    db: InMemoryDB
    users: InMemoryUserRepository
    categories: InMemoryCategoryRepository
    tasks: InMemoryTaskRepository
    solves: InMemorySolveRepository
    proposals: InMemoryProposalRepository
    writeups: InMemoryWriteupRepository
    login_uc: LoginUserUseCase
    register_uc: RegisterUserUseCase
    category_uc: CategoryOverviewUseCase
    task_detail_uc: TaskDetailUseCase
    category_tasks_uc: CategoryTasksUseCase
    titles_uc: TasksByTitleUseCase
    submit_flag_uc: SubmitFlagUseCase
    forfeit_uc: ForfeitTaskUseCase
    leaderboard_uc: LeaderboardUseCase
    list_suggestions_uc: ListSuggestionsUseCase
    submit_suggestion_uc: SubmitSuggestionUseCase
    admin_dashboard_uc: AdminDashboardUseCase
    admin_tasks_uc: AdminTasksUseCase
    admin_add_task_uc: AdminAddTaskUseCase
    admin_edit_task_uc: AdminEditTaskUseCase
    admin_delete_task_uc: AdminDeleteTaskUseCase
    admin_proposals_uc: AdminProposalsUseCase
    admin_approve_uc: AdminApproveProposalUseCase
    admin_reject_uc: AdminRejectProposalUseCase
    list_writeups_uc: ListWriteupsUseCase
    submit_writeup_uc: SubmitWriteupUseCase


def build_container() -> Container:
    db = create_db()
    users = InMemoryUserRepository(db)
    categories = InMemoryCategoryRepository(db)
    tasks = InMemoryTaskRepository(db)
    solves = InMemorySolveRepository(db)
    proposals = InMemoryProposalRepository(db)
    writeups = InMemoryWriteupRepository(db)

    _seed(users, categories, tasks)

    return Container(
        db=db,
        users=users,
        categories=categories,
        tasks=tasks,
        solves=solves,
        proposals=proposals,
        writeups=writeups,
        login_uc=LoginUserUseCase(users),
        register_uc=RegisterUserUseCase(users),
        category_uc=CategoryOverviewUseCase(categories, tasks, solves),
        task_detail_uc=TaskDetailUseCase(categories, tasks, solves),
        category_tasks_uc=CategoryTasksUseCase(categories, tasks, solves),
        titles_uc=TasksByTitleUseCase(tasks, solves),
        submit_flag_uc=SubmitFlagUseCase(tasks, solves),
        forfeit_uc=ForfeitTaskUseCase(tasks, solves),
        leaderboard_uc=LeaderboardUseCase(users, tasks, solves),
        list_suggestions_uc=ListSuggestionsUseCase(proposals, categories),
        submit_suggestion_uc=SubmitSuggestionUseCase(proposals, tasks),
        admin_dashboard_uc=AdminDashboardUseCase(users, tasks, proposals),
        admin_tasks_uc=AdminTasksUseCase(tasks, categories),
        admin_add_task_uc=AdminAddTaskUseCase(tasks),
        admin_edit_task_uc=AdminEditTaskUseCase(tasks),
        admin_delete_task_uc=AdminDeleteTaskUseCase(tasks, solves, writeups),
        admin_proposals_uc=AdminProposalsUseCase(proposals, categories),
        admin_approve_uc=AdminApproveProposalUseCase(proposals, tasks),
        admin_reject_uc=AdminRejectProposalUseCase(proposals),
        list_writeups_uc=ListWriteupsUseCase(writeups, tasks, users, solves),
        submit_writeup_uc=SubmitWriteupUseCase(writeups, solves),
    )


def _seed(users: InMemoryUserRepository, categories: InMemoryCategoryRepository, tasks: InMemoryTaskRepository) -> None:
    if not users.get_by_username("admin"):
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        users.add(User(id=0, username="admin", password_hash=hashed, role="admin"))

    osint_cat = categories.get_by_name("OSINT")
    if not osint_cat:
        osint_cat = categories.add(Category(id=0, name="OSINT"))

    beginner_cat = categories.get_by_name("Beginner")
    if not beginner_cat:
        beginner_cat = categories.add(Category(id=0, name="Beginner"))

    _ensure_task(
        tasks,
        title="Анонимный спортсмен",
        description="Привет, я слышал, что ты можешь вычислить человека по IP...",
        flag_bytes=b"seculeti{Pr0f1t}",
        points=1000,
        category_id=osint_cat.id,
    )

    _ensure_task(
        tasks,
        title="Без комментариев",
        description="Все с чего-то начинают, даже если у тебя нет инструментов для этого.",
        flag_bytes=b"seculeti{Plz_D0nt_C0mm3nt_th1$}",
        points=15,
        category_id=beginner_cat.id,
    )

    _ensure_task(
        tasks,
        title="Little Osinter",
        description="Команда seculeti уже десятый раз меняет название своей группы...",
        flag_bytes=b"seculeti{3350971088}",
        points=25,
        category_id=beginner_cat.id,
    )

    _ensure_task(
        tasks,
        title="Крипто-ключ",
        description="Сколько раз говорить ему не оставлять пароли на столе..",
        flag_bytes=b"seculeti{Th4t$T0oCl1ch3N0tEv3rCrypt0}",
        points=15,
        category_id=beginner_cat.id,
    )


def _ensure_task(
    tasks: InMemoryTaskRepository,
    title: str,
    description: str,
    flag_bytes: bytes,
    points: int,
    category_id: int,
) -> Task:
    existing = tasks.get_by_title(title)
    if existing:
        if existing.points != points:
            existing.points = points
            tasks.update(existing)
        return existing
    flag_hash = bcrypt.hashpw(flag_bytes, bcrypt.gensalt()).decode("utf-8")
    task = Task(
        id=0,
        title=title,
        description=description,
        flag_hash=flag_hash,
        points=points,
        category_id=category_id,
    )
    return tasks.add(task)