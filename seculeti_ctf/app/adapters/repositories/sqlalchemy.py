from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from ...domain.entities import Category, Proposal, Solve, Task, User, Writeup
from ...domain.repositories import (
    CategoryRepository,
    ProposalRepository,
    SolveRepository,
    TaskRepository,
    UserRepository,
    WriteupRepository,
)
from ...infrastructure.db import (
    CategoryModel,
    ProposalModel,
    SolveModel,
    TaskModel,
    UserModel,
    WriteupModel,
)


def _user_from_model(model: UserModel) -> User:
    return User(id=model.id, username=model.username, password_hash=model.password, role=model.role)


def _category_from_model(model: CategoryModel) -> Category:
    return Category(id=model.id, name=model.name)


def _task_from_model(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        flag_hash=model.flag_hash,
        points=model.points,
        category_id=model.category_id,
    )


def _solve_from_model(model: SolveModel) -> Solve:
    return Solve(
        id=model.id,
        user_id=model.user_id,
        task_id=model.task_id,
        solved_at=model.solved_at,
        points_awarded=model.points_awarded,
        is_forfeit=model.is_forfeit,
    )


def _proposal_from_model(model: ProposalModel) -> Proposal:
    return Proposal(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        description=model.description,
        category_id=model.category_id,
        difficulty=model.difficulty,
        points=model.points,
        flag=model.flag,
        hints=model.hints or "",
        status=model.status,
        created_at=model.created_at,
    )


def _writeup_from_model(model: WriteupModel) -> Writeup:
    return Writeup(
        id=model.id,
        user_id=model.user_id,
        task_id=model.task_id,
        content=model.content,
        created_at=model.created_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        model = UserModel(username=user.username, password=user.password_hash, role=user.role)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        user.id = model.id
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self._session.get(UserModel, user_id)
        return _user_from_model(model) if model else None

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _user_from_model(model) if model else None

    def list_all(self) -> Iterable[User]:
        stmt = select(UserModel).order_by(UserModel.id.asc())
        return [_user_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def count(self) -> int:
        return self._session.query(UserModel).count()


class SqlAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, category: Category) -> Category:
        model = CategoryModel(name=category.name)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        category.id = model.id
        return category

    def get_by_id(self, category_id: int) -> Optional[Category]:
        model = self._session.get(CategoryModel, category_id)
        return _category_from_model(model) if model else None

    def get_by_name(self, name: str) -> Optional[Category]:
        stmt = select(CategoryModel).where(CategoryModel.name == name)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _category_from_model(model) if model else None

    def list_all(self) -> Iterable[Category]:
        stmt = select(CategoryModel).order_by(CategoryModel.id.asc())
        return [_category_from_model(m) for m in self._session.execute(stmt).scalars().all()]


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, task: Task) -> Task:
        model = TaskModel(
            title=task.title,
            description=task.description,
            flag_hash=task.flag_hash,
            points=task.points,
            category_id=task.category_id,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        task.id = model.id
        return task

    def update(self, task: Task) -> None:
        model = self._session.get(TaskModel, task.id)
        if not model:
            return
        model.title = task.title
        model.description = task.description
        model.flag_hash = task.flag_hash
        model.points = task.points
        model.category_id = task.category_id
        self._session.commit()

    def delete(self, task_id: int) -> None:
        model = self._session.get(TaskModel, task_id)
        if not model:
            return
        self._session.delete(model)
        self._session.commit()

    def get_by_id(self, task_id: int) -> Optional[Task]:
        model = self._session.get(TaskModel, task_id)
        return _task_from_model(model) if model else None

    def get_by_title(self, title: str) -> Optional[Task]:
        stmt = select(TaskModel).where(TaskModel.title == title)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _task_from_model(model) if model else None

    def list_all(self) -> Iterable[Task]:
        stmt = select(TaskModel).order_by(TaskModel.id.asc())
        return [_task_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def list_by_category_id(self, category_id: int) -> Iterable[Task]:
        stmt = select(TaskModel).where(TaskModel.category_id == category_id).order_by(TaskModel.id.asc())
        return [_task_from_model(m) for m in self._session.execute(stmt).scalars().all()]


class SqlAlchemySolveRepository(SolveRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, solve: Solve) -> Solve:
        model = SolveModel(
            user_id=solve.user_id,
            task_id=solve.task_id,
            solved_at=solve.solved_at,
            points_awarded=solve.points_awarded,
            is_forfeit=solve.is_forfeit,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        solve.id = model.id
        return solve

    def update(self, solve: Solve) -> None:
        model = self._session.get(SolveModel, solve.id)
        if not model:
            return
        model.solved_at = solve.solved_at
        model.points_awarded = solve.points_awarded
        model.is_forfeit = solve.is_forfeit
        self._session.commit()

    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Solve]:
        stmt = select(SolveModel).where(SolveModel.user_id == user_id, SolveModel.task_id == task_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _solve_from_model(model) if model else None

    def list_by_user(self, user_id: int) -> Iterable[Solve]:
        stmt = select(SolveModel).where(SolveModel.user_id == user_id).order_by(SolveModel.id.asc())
        return [_solve_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def list_all(self) -> Iterable[Solve]:
        stmt = select(SolveModel).order_by(SolveModel.id.asc())
        return [_solve_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def delete_by_task(self, task_id: int) -> None:
        stmt = select(SolveModel).where(SolveModel.task_id == task_id)
        models = self._session.execute(stmt).scalars().all()
        for model in models:
            self._session.delete(model)
        if models:
            self._session.commit()


class SqlAlchemyProposalRepository(ProposalRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, proposal: Proposal) -> Proposal:
        model = ProposalModel(
            user_id=proposal.user_id,
            title=proposal.title,
            description=proposal.description,
            category_id=proposal.category_id,
            difficulty=proposal.difficulty,
            points=proposal.points,
            flag=proposal.flag,
            hints=proposal.hints,
            status=proposal.status,
            created_at=proposal.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        proposal.id = model.id
        return proposal

    def update(self, proposal: Proposal) -> None:
        model = self._session.get(ProposalModel, proposal.id)
        if not model:
            return
        model.title = proposal.title
        model.description = proposal.description
        model.category_id = proposal.category_id
        model.difficulty = proposal.difficulty
        model.points = proposal.points
        model.flag = proposal.flag
        model.hints = proposal.hints
        model.status = proposal.status
        self._session.commit()

    def get_by_id(self, proposal_id: int) -> Optional[Proposal]:
        model = self._session.get(ProposalModel, proposal_id)
        return _proposal_from_model(model) if model else None

    def get_by_title(self, title: str) -> Optional[Proposal]:
        stmt = select(ProposalModel).where(ProposalModel.title == title)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _proposal_from_model(model) if model else None

    def list_by_user(self, user_id: int) -> Iterable[Proposal]:
        stmt = select(ProposalModel).where(ProposalModel.user_id == user_id).order_by(ProposalModel.id.asc())
        return [_proposal_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def list_pending(self) -> Iterable[Proposal]:
        stmt = select(ProposalModel).where(ProposalModel.status == "pending").order_by(ProposalModel.id.asc())
        return [_proposal_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def list_all(self) -> Iterable[Proposal]:
        stmt = select(ProposalModel).order_by(ProposalModel.id.asc())
        return [_proposal_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def count_pending(self) -> int:
        return self._session.query(ProposalModel).filter(ProposalModel.status == "pending").count()


class SqlAlchemyWriteupRepository(WriteupRepository):
    def __init__(self, session: scoped_session) -> None:
        self._session = session

    def add(self, writeup: Writeup) -> Writeup:
        model = WriteupModel(
            user_id=writeup.user_id,
            task_id=writeup.task_id,
            content=writeup.content,
            created_at=writeup.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        writeup.id = model.id
        return writeup

    def get_by_user_task(self, user_id: int, task_id: int) -> Optional[Writeup]:
        stmt = select(WriteupModel).where(WriteupModel.user_id == user_id, WriteupModel.task_id == task_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        return _writeup_from_model(model) if model else None

    def list_by_task_ids(self, task_ids: Iterable[int]) -> Iterable[Writeup]:
        ids = list(task_ids)
        if not ids:
            return []
        stmt = select(WriteupModel).where(WriteupModel.task_id.in_(ids)).order_by(WriteupModel.id.asc())
        return [_writeup_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def list_by_task_id(self, task_id: int) -> Iterable[Writeup]:
        stmt = select(WriteupModel).where(WriteupModel.task_id == task_id).order_by(WriteupModel.id.asc())
        return [_writeup_from_model(m) for m in self._session.execute(stmt).scalars().all()]

    def delete_by_task(self, task_id: int) -> None:
        stmt = select(WriteupModel).where(WriteupModel.task_id == task_id)
        models = self._session.execute(stmt).scalars().all()
        for model in models:
            self._session.delete(model)
        if models:
            self._session.commit()
