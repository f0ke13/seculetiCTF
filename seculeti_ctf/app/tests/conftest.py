# seculeti_ctf/app/tests/conftest.py

import sys
from pathlib import Path

# Добавляем путь к проекту
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

import pytest
from app.infrastructure.db import create_db, InMemoryDB
from app.adapters.repositories.in_memory import (
    InMemoryUserRepository,
    InMemoryCategoryRepository,
    InMemoryTaskRepository,
    InMemorySolveRepository,
    InMemoryProposalRepository,
    InMemoryWriteupRepository,
)
from app.domain.entities import User, Category, Task, Solve
from app.usecases.leaderboard import LeaderboardUseCase
import bcrypt
from datetime import datetime


@pytest.fixture
def in_memory_db():
    """Создает in-memory базу данных"""
    return create_db()


@pytest.fixture
def user_repo(in_memory_db):
    """Репозиторий пользователей"""
    return InMemoryUserRepository(in_memory_db)


@pytest.fixture
def category_repo(in_memory_db):
    """Репозиторий категорий"""
    return InMemoryCategoryRepository(in_memory_db)


@pytest.fixture
def task_repo(in_memory_db):
    """Репозиторий задач"""
    return InMemoryTaskRepository(in_memory_db)


@pytest.fixture
def solve_repo(in_memory_db):
    """Репозиторий решений"""
    return InMemorySolveRepository(in_memory_db)


@pytest.fixture
def test_user(user_repo):
    """Создает тестового пользователя"""
    hashed = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode("utf-8")
    user = User(id=0, username="testuser", password_hash=hashed, role="user")
    return user_repo.add(user)


@pytest.fixture
def test_category(category_repo):
    """Создает тестовую категорию"""
    category = Category(id=0, name="Test Category")
    return category_repo.add(category)


@pytest.fixture
def test_task(task_repo, test_category):
    """Создает тестовую задачу"""
    flag_hash = bcrypt.hashpw(b"testflag{test}", bcrypt.gensalt()).decode("utf-8")
    task = Task(
        id=0,
        title="Test Task",
        description="Test description",
        flag_hash=flag_hash,
        points=100,
        category_id=test_category.id
    )
    return task_repo.add(task)


@pytest.fixture
def test_solve(solve_repo, test_user, test_task):
    """Создает тестовое решение"""
    solve = Solve(
        id=0,
        user_id=test_user.id,
        task_id=test_task.id,
        solved_at=datetime.now(),
        points_awarded=100,
        is_forfeit=False
    )
    return solve_repo.add(solve)


@pytest.fixture
def leaderboard_use_case(user_repo, task_repo, solve_repo):
    """Use case для лидерборда"""
    return LeaderboardUseCase(user_repo, task_repo, solve_repo)


@pytest.fixture
def flask_test_client():
    """Создает тестовый клиент Flask с in-memory репозиториями"""
    from app.infrastructure.flask_app import create_app
    from app.infrastructure.di import build_container
    from app.adapters.repositories.in_memory import (
        InMemoryUserRepository,
        InMemoryCategoryRepository,
        InMemoryTaskRepository,
        InMemorySolveRepository,
        InMemoryProposalRepository,
        InMemoryWriteupRepository,
    )
    from app.infrastructure.db import create_db
    
    app = create_app()
    app.config['TESTING'] = True
    
    # Создаем in-memory БД и репозитории
    db = create_db()
    app.container = type('Container', (), {})()
    app.container.users = InMemoryUserRepository(db)
    app.container.categories = InMemoryCategoryRepository(db)
    app.container.tasks = InMemoryTaskRepository(db)
    app.container.solves = InMemorySolveRepository(db)
    app.container.proposals = InMemoryProposalRepository(db)
    app.container.writeups = InMemoryWriteupRepository(db)
    
    # Добавляем тестовые данные
    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
    admin = User(id=0, username="admin", password_hash=hashed, role="admin")
    app.container.users.add(admin)
    
    category = Category(id=0, name="Beginner")
    app.container.categories.add(category)
    
    flag_hash = bcrypt.hashpw(b"seculeti{test}", bcrypt.gensalt()).decode("utf-8")
    task = Task(id=0, title="Test", description="Test", flag_hash=flag_hash, points=100, category_id=category.id)
    app.container.tasks.add(task)
    
    return app.test_client()