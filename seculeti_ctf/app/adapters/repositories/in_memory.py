from __future__ import annotations

from typing import Iterable, Optional

from ...domain.entities import Category, Proposal, Solve, Task, User, Writeup
from ...domain.repositories import (
    CategoryRepository,
    ProposalRepository,
    SolveRepository,
    TaskRepository,
    UserRepository,
    WriteupRepository,
)
from ...infrastructure.db import InMemoryDB


class InMemoryUserRepository(UserRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, user: User) -> User:
        new_id = self._db.next_id("users")
        user.id = new_id
        self._db.users[new_id] = user
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._db.users.get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return next((u for u in self._db.users.values() if u.username == username), None)

    def list_all(self) -> Iterable[User]:
        return list(self._db.users.values())

    def count(self) -> int:
        return len(self._db.users)


class InMemoryCategoryRepository(CategoryRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, category: Category) -> Category:
        new_id = self._db.next_id("categories")
        category.id = new_id
        self._db.categories[new_id] = category
        return category

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self._db.categories.get(category_id)

    def get_by_name(self, name: str) -> Optional[Category]:
        return next((c for c in self._db.categories.values() if c.name == name), None)

    def list_all(self) -> Iterable[Category]:
        return list(self._db.categories.values())


class InMemoryTaskRepository(TaskRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, task: Task) -> Task:
        new_id = self._db.next_id("tasks")
        task.id = new_id
        self._db.tasks[new_id] = task
        return task

    def update(self, task: Task) -> None:
        self._db.tasks[task.id] = task

    def delete(self, task_id: int) -> None:
        self._db.tasks.pop(task_id, None)

    def get_by_id(self, task_id: int) -> Optional[Task]:
        return self._db.tasks.get(task_id)

    def get_by_title(self, title: str) -> Optional[Task]:
        return next((t for t in self._db.tasks.values() if t.title == title), None)

    def list_all(self) -> Iterable[Task]:
        return list(self._db.tasks.values())

    def list_by_category_id(self, category_id: int) -> Iterable[Task]:
        return [t for t in self._db.tasks.values() if t.category_id == category_id]


class InMemorySolveRepository(SolveRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, solve: Solve) -> Solve:
        new_id = self._db.next_id("solves")
        solve.id = new_id
        self._db.solves[new_id] = solve
        return solve

    def update(self, solve: Solve) -> None:
        self._db.solves[solve.id] = solve

    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Solve]:
        return next(
            (s for s in self._db.solves.values() if s.user_id == user_id and s.task_id == task_id),
            None,
        )

    def list_by_user(self, user_id: int) -> Iterable[Solve]:
        return [s for s in self._db.solves.values() if s.user_id == user_id]

    def list_all(self) -> Iterable[Solve]:
        return list(self._db.solves.values())

    def delete_by_task(self, task_id: int) -> None:
        to_delete = [sid for sid, s in self._db.solves.items() if s.task_id == task_id]
        for sid in to_delete:
            self._db.solves.pop(sid, None)


class InMemoryProposalRepository(ProposalRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, proposal: Proposal) -> Proposal:
        new_id = self._db.next_id("proposals")
        proposal.id = new_id
        self._db.proposals[new_id] = proposal
        return proposal

    def update(self, proposal: Proposal) -> None:
        self._db.proposals[proposal.id] = proposal

    def get_by_id(self, proposal_id: int) -> Optional[Proposal]:
        return self._db.proposals.get(proposal_id)

    def get_by_title(self, title: str) -> Optional[Proposal]:
        return next((p for p in self._db.proposals.values() if p.title == title), None)

    def list_by_user(self, user_id: int) -> Iterable[Proposal]:
        return [p for p in self._db.proposals.values() if p.user_id == user_id]

    def list_pending(self) -> Iterable[Proposal]:
        return [p for p in self._db.proposals.values() if p.status == "pending"]

    def list_all(self) -> Iterable[Proposal]:
        return list(self._db.proposals.values())

    def count_pending(self) -> int:
        return len([p for p in self._db.proposals.values() if p.status == "pending"])


class InMemoryWriteupRepository(WriteupRepository):
    def __init__(self, db: InMemoryDB) -> None:
        self._db = db

    def add(self, writeup: Writeup) -> Writeup:
        new_id = self._db.next_id("writeups")
        writeup.id = new_id
        self._db.writeups[new_id] = writeup
        return writeup

    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Writeup]:
        return next(
            (w for w in self._db.writeups.values() if w.user_id == user_id and w.task_id == task_id),
            None,
        )

    def list_by_task_ids(self, task_ids: Iterable[int]) -> Iterable[Writeup]:
        return [w for w in self._db.writeups.values() if w.task_id in task_ids]

    def list_by_task_id(self, task_id: int) -> Iterable[Writeup]:
        return [w for w in self._db.writeups.values() if w.task_id == task_id]

    def delete_by_task(self, task_id: int) -> None:
        to_delete = [wid for wid, w in self._db.writeups.items() if w.task_id == task_id]
        for wid in to_delete:
            self._db.writeups.pop(wid, None)
