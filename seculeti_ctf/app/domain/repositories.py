from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from .entities import User, Category, Task, Solve, Proposal, Writeup


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[User]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError


class CategoryRepository(ABC):
    @abstractmethod
    def add(self, category: Category) -> Category:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[Category]:
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Category]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[Category]:
        raise NotImplementedError


class TaskRepository(ABC):
    @abstractmethod
    def add(self, task: Task) -> Task:
        raise NotImplementedError

    @abstractmethod
    def update(self, task: Task) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, task_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_by_title(self, title: str) -> Optional[Task]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[Task]:
        raise NotImplementedError

    @abstractmethod
    def list_by_category_id(self, category_id: int) -> Iterable[Task]:
        raise NotImplementedError


class SolveRepository(ABC):
    @abstractmethod
    def add(self, solve: Solve) -> Solve:
        raise NotImplementedError

    @abstractmethod
    def update(self, solve: Solve) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Solve]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> Iterable[Solve]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[Solve]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_task(self, task_id: int) -> None:
        raise NotImplementedError


class ProposalRepository(ABC):
    @abstractmethod
    def add(self, proposal: Proposal) -> Proposal:
        raise NotImplementedError

    @abstractmethod
    def update(self, proposal: Proposal) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, proposal_id: int) -> Optional[Proposal]:
        raise NotImplementedError

    @abstractmethod
    def get_by_title(self, title: str) -> Optional[Proposal]:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: int) -> Iterable[Proposal]:
        raise NotImplementedError

    @abstractmethod
    def list_pending(self) -> Iterable[Proposal]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> Iterable[Proposal]:
        raise NotImplementedError

    @abstractmethod
    def count_pending(self) -> int:
        raise NotImplementedError


class WriteupRepository(ABC):
    @abstractmethod
    def add(self, writeup: Writeup) -> Writeup:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Writeup]:
        raise NotImplementedError

    @abstractmethod
    def list_by_task_ids(self, task_ids: Iterable[int]) -> Iterable[Writeup]:
        raise NotImplementedError

    @abstractmethod
    def list_by_task_id(self, task_id: int) -> Iterable[Writeup]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_task(self, task_id: int) -> None:
        raise NotImplementedError