from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..domain.entities import Category, Proposal, Solve, Task, User, Writeup


@dataclass
class InMemoryDB:
    users: Dict[int, User] = field(default_factory=dict)
    categories: Dict[int, Category] = field(default_factory=dict)
    tasks: Dict[int, Task] = field(default_factory=dict)
    solves: Dict[int, Solve] = field(default_factory=dict)
    proposals: Dict[int, Proposal] = field(default_factory=dict)
    writeups: Dict[int, Writeup] = field(default_factory=dict)
    _counters: Dict[str, int] = field(
        default_factory=lambda: {
            "users": 0,
            "categories": 0,
            "tasks": 0,
            "solves": 0,
            "proposals": 0,
            "writeups": 0,
        }
    )

    def next_id(self, key: str) -> int:
        self._counters[key] += 1
        return self._counters[key]


def create_db() -> InMemoryDB:
    return InMemoryDB()
