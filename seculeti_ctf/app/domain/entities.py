from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str = "user"


@dataclass
class Category:
    id: int
    name: str


@dataclass
class Task:
    id: int
    title: str
    description: str
    flag_hash: str
    points: int
    category_id: int


@dataclass
class Solve:
    id: int
    user_id: int
    task_id: int
    solved_at: datetime
    points_awarded: int
    is_forfeit: bool = False


@dataclass
class Proposal:
    id: int
    user_id: int
    title: str
    description: str
    category_id: int
    difficulty: str
    points: int
    flag: str
    hints: str
    status: str
    created_at: datetime


@dataclass
class Writeup:
    id: int
    user_id: int
    task_id: int
    content: str
    created_at: datetime
