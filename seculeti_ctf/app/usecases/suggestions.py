from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from ..domain.entities import Proposal
from ..domain.exceptions import DuplicateError, ValidationError
from ..domain.repositories import CategoryRepository, ProposalRepository, TaskRepository


@dataclass
class SuggestionView:
    proposals: List[Proposal]
    categories: list


class ListSuggestionsUseCase:
    def __init__(self, proposals: ProposalRepository, categories: CategoryRepository) -> None:
        self._proposals = proposals
        self._categories = categories

    def execute(self, user_id: int) -> SuggestionView:
        return SuggestionView(
            proposals=list(self._proposals.list_by_user(user_id)),
            categories=list(self._categories.list_all()),
        )


class SubmitSuggestionUseCase:
    def __init__(self, proposals: ProposalRepository, tasks: TaskRepository) -> None:
        self._proposals = proposals
        self._tasks = tasks

    def execute(
        self,
        user_id: int,
        title: str,
        category_id: int,
        description: str,
        points: int,
        flag: str,
        hints: str = "",
        difficulty: str = "medium",
    ) -> Proposal:
        if not title or not category_id or not description or not flag:
            raise ValidationError("Заполните все обязательные поля")
        if self._proposals.get_by_title(title):
            raise DuplicateError("Задача с таким названием уже существует")
        if self._tasks.get_by_title(title):
            raise DuplicateError("Задача с таким названием уже существует")

        proposal = Proposal(
            id=0,
            user_id=user_id,
            title=title,
            description=description,
            category_id=category_id,
            difficulty=difficulty or "medium",
            points=points if isinstance(points, int) else 100,
            flag=flag,
            hints=hints or "",
            status="pending",
            created_at=datetime.utcnow(),
        )
        return self._proposals.add(proposal)