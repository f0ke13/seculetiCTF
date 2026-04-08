from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from ..domain.entities import Category, Task
from ..domain.exceptions import NotFoundError
from ..domain.repositories import CategoryRepository, SolveRepository, TaskRepository


@dataclass
class CategoryOverview:
    categories: List[Category]
    tasks: List[Task]
    solved_task_ids: List[int]


class CategoryOverviewUseCase:
    def __init__(
        self,
        categories: CategoryRepository,
        tasks: TaskRepository,
        solves: SolveRepository,
    ) -> None:
        self._categories = categories
        self._tasks = tasks
        self._solves = solves

    def execute(self, user_id: int) -> CategoryOverview:
        categories = list(self._categories.list_all())
        tasks = list(self._tasks.list_all())
        solves = [s for s in self._solves.list_by_user(user_id) if not s.is_forfeit]
        solved_ids = [s.task_id for s in solves]
        return CategoryOverview(categories=categories, tasks=tasks, solved_task_ids=solved_ids)


@dataclass
class TaskDetail:
    category: Category
    task: Task
    solved: bool
    forfeit: bool


class TaskDetailUseCase:
    def __init__(
        self,
        categories: CategoryRepository,
        tasks: TaskRepository,
        solves: SolveRepository,
    ) -> None:
        self._categories = categories
        self._tasks = tasks
        self._solves = solves

    def execute(self, user_id: int, category_name: str, task_name: str) -> TaskDetail:
        category = self._find_category(category_name)
        task = self._find_task(category.id, task_name)
        solve = self._solves.get_by_user_task(user_id, task.id)
        solved = solve is not None and not solve.is_forfeit
        forfeit = solve is not None and solve.is_forfeit
        return TaskDetail(category=category, task=task, solved=solved, forfeit=forfeit)

    def _find_category(self, category_name: str) -> Category:
        for category in self._categories.list_all():
            if category.name.lower() == category_name.lower():
                return category
        raise NotFoundError("Категория не найдена")

    def _find_task(self, category_id: int, task_name: str) -> Task:
        normalized = task_name.lower().replace("_", " ")
        for task in self._tasks.list_by_category_id(category_id):
            if task.title.lower() == normalized:
                return task
        raise NotFoundError("Задание не найдено")


class TasksByTitleUseCase:
    def __init__(self, tasks: TaskRepository, solves: SolveRepository) -> None:
        self._tasks = tasks
        self._solves = solves

    def execute(self, user_id: int, titles: Iterable[str]) -> List[Tuple[Optional[Task], bool]]:
        results: List[Tuple[Optional[Task], bool]] = []
        for title in titles:
            task = self._tasks.get_by_title(title)
            if not task:
                results.append((None, False))
                continue
            solved = self._solves.get_by_user_task(user_id, task.id)
            results.append((task, solved is not None and not solved.is_forfeit))
        return results