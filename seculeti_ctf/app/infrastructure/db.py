from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from ..domain.entities import Category, Proposal, Solve, Task, User, Writeup

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")


class CategoryModel(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    flag_hash = Column(String(255), nullable=False)
    points = Column(Integer, default=100)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)


class SolveModel(Base):
    __tablename__ = "solves"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    solved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    points_awarded = Column(Integer, default=0)
    is_forfeit = Column(Boolean, default=False)


class ProposalModel(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    difficulty = Column(String(50), default="medium")
    points = Column(Integer, default=100)
    flag = Column(String(255), nullable=False)
    hints = Column(Text, default="")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WriteupModel(Base):
    __tablename__ = "writeups"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


@dataclass
class Database:
    engine: Engine
    session: scoped_session


def build_db(db_url: str) -> Database:
    engine = create_engine(db_url, pool_pre_ping=True)
    session_factory = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
    return Database(engine=engine, session=session_factory)


def init_db(db: Database) -> None:
    Base.metadata.create_all(bind=db.engine)


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
