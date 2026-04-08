# seculeti_ctf/app/tests/test_inmemory.py

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))

import pytest
import bcrypt
from datetime import datetime, timezone

from app.domain.entities import User, Category, Task, Solve
from app.domain.exceptions import NotFoundError, DuplicateError, ValidationError, AuthError
from app.usecases.leaderboard import LeaderboardUseCase
from app.usecases.tasks import CategoryOverviewUseCase, CategoryTasksUseCase, TaskDetailUseCase
from app.usecases.submissions import SubmitFlagUseCase, ForfeitTaskUseCase
from app.usecases.auth import RegisterUserUseCase, LoginUserUseCase
from app.usecases.suggestions import ListSuggestionsUseCase, SubmitSuggestionUseCase
from app.usecases.writeups import ListWriteupsUseCase, SubmitWriteupUseCase
from app.usecases.admin import (
    AdminDashboardUseCase, AdminTasksUseCase, AdminAddTaskUseCase,
    AdminEditTaskUseCase, AdminDeleteTaskUseCase, AdminProposalsUseCase,
    AdminApproveProposalUseCase, AdminRejectProposalUseCase
)


# ============== FIXTURES ==============

@pytest.fixture
def in_memory_db():
    from app.infrastructure.db import create_db
    return create_db()


@pytest.fixture
def user_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemoryUserRepository
    return InMemoryUserRepository(in_memory_db)


@pytest.fixture
def category_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemoryCategoryRepository
    return InMemoryCategoryRepository(in_memory_db)


@pytest.fixture
def task_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemoryTaskRepository
    return InMemoryTaskRepository(in_memory_db)


@pytest.fixture
def solve_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemorySolveRepository
    return InMemorySolveRepository(in_memory_db)


@pytest.fixture
def proposal_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemoryProposalRepository
    return InMemoryProposalRepository(in_memory_db)


@pytest.fixture
def writeup_repo(in_memory_db):
    from app.adapters.repositories.in_memory import InMemoryWriteupRepository
    return InMemoryWriteupRepository(in_memory_db)


@pytest.fixture
def regular_user(user_repo):
    hashed = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode("utf-8")
    user = User(id=0, username="player", password_hash=hashed, role="user")
    return user_repo.add(user)


@pytest.fixture
def admin_user(user_repo):
    hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
    user = User(id=0, username="admin", password_hash=hashed, role="admin")
    return user_repo.add(user)


@pytest.fixture
def test_category(category_repo):
    category = Category(id=0, name="OSINT")
    return category_repo.add(category)


@pytest.fixture
def test_task(task_repo, test_category):
    flag_hash = bcrypt.hashpw(b"seculeti{test_flag_123}", bcrypt.gensalt()).decode("utf-8")
    task = Task(
        id=0,
        title="Анонимный спортсмен",
        description="Привет, я слышал, что ты можешь вычислить человека по IP...\nСсылка на исходники: https://disk.yandex.ru/i/AgPmrqkI8C5Ifg",
        flag_hash=flag_hash,
        points=1000,
        category_id=test_category.id
    )
    return task_repo.add(task)


# ============== ТЕСТ 1: ПОЛНЫЙ ВОРКФЛОУ ==============

def test_complete_workflow(user_repo, category_repo, task_repo, solve_repo, regular_user, test_category, test_task):
    """Полный воркфлоу"""
    category_uc = CategoryOverviewUseCase(category_repo, task_repo, solve_repo)
    overview = category_uc.execute(user_id=regular_user.id)
    assert len(overview.categories) >= 1
    assert len(overview.solved_task_ids) == 0

    category_tasks_uc = CategoryTasksUseCase(category_repo, task_repo, solve_repo)
    category_view = category_tasks_uc.execute(user_id=regular_user.id, category_name="OSINT")
    assert category_view.category.name == "OSINT"
    assert len(category_view.tasks) >= 1

    task_detail_uc = TaskDetailUseCase(category_repo, task_repo, solve_repo)
    task_detail = task_detail_uc.execute(user_id=regular_user.id, category_name="OSINT", task_name="Анонимный спортсмен")
    assert task_detail.task.title == "Анонимный спортсмен"
    assert task_detail.solved is False
    assert "disk.yandex.ru" in task_detail.task.description

    submit_uc = SubmitFlagUseCase(task_repo, solve_repo)
    result = submit_uc.execute(user_id=regular_user.id, flag="seculeti{test_flag_123}")
    assert result.success is True
    assert result.points == 1000

    leaderboard_uc = LeaderboardUseCase(user_repo, task_repo, solve_repo)
    leaderboard = leaderboard_uc.execute()
    player_found = False
    for player in leaderboard.players:
        if player.username == regular_user.username:
            player_found = True
            assert player.score == 1000
            assert player.solved == 1
            break
    assert player_found

    task_detail_after = task_detail_uc.execute(user_id=regular_user.id, category_name="OSINT", task_name="Анонимный спортсмен")
    assert task_detail_after.solved is True


# ============== ТЕСТЫ: AUTH ==============

def test_auth_register_success(user_repo):
    """POST /register, Успех: Успешная регистрация нового пользователя"""
    uc = RegisterUserUseCase(user_repo)
    user = uc.execute(username="newuser", password="secret123")
    assert user.username == "newuser"
    assert user.role == "user"
    assert user.id is not None


def test_auth_register_duplicate_error(user_repo, regular_user):
    """POST /register, Логическая ошибка: регистрация с существующим username"""
    uc = RegisterUserUseCase(user_repo)
    with pytest.raises(DuplicateError):
        uc.execute(username=regular_user.username, password="anypass")


def test_auth_register_validation_error(user_repo):
    """POST /register, Логическая ошибка: Регистрация с пустыми полями вызывает ValidationError"""
    uc = RegisterUserUseCase(user_repo)
    with pytest.raises(ValidationError):
        uc.execute(username="", password="")


def test_auth_login_success(user_repo, regular_user):
    """POST /login, Успех: Успешный вход с правильными учетными данными"""
    uc = LoginUserUseCase(user_repo)
    user = uc.execute(username=regular_user.username, password="user123")
    assert user.username == regular_user.username


def test_auth_login_wrong_password(user_repo, regular_user):
    """POST /login, Логическая ошибка: Вход с неверным паролем вызывает AuthError"""
    uc = LoginUserUseCase(user_repo)
    with pytest.raises(AuthError):
        uc.execute(username=regular_user.username, password="wrongpass")


def test_auth_login_nonexistent_user(user_repo):
    """POST /login, Логическая ошибка: вход с несуществующим пользователем вызывает AuthError"""
    uc = LoginUserUseCase(user_repo)
    with pytest.raises(AuthError):
        uc.execute(username="ghost", password="pass")


# ============== ТЕСТЫ: TASKS ==============

def test_tasks_category_overview_success(user_repo, category_repo, task_repo, solve_repo, regular_user):
    """GET /category, Успех: Успешное получение списка категорий и прогресса пользователя"""
    uc = CategoryOverviewUseCase(category_repo, task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id)
    assert hasattr(result, 'categories')
    assert hasattr(result, 'tasks')
    assert hasattr(result, 'solved_task_ids')


def test_tasks_category_overview_empty_tasks(user_repo, category_repo, solve_repo, regular_user):
    """GET /category, Логическая ошибка: Получение прогресса когда нет задач возвращает пустые списки"""
    from app.infrastructure.db import create_db
    new_db = create_db()
    from app.adapters.repositories.in_memory import InMemoryTaskRepository
    empty_task_repo = InMemoryTaskRepository(new_db)
    uc = CategoryOverviewUseCase(category_repo, empty_task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id)
    assert len(result.tasks) == 0
    assert len(result.solved_task_ids) == 0


def test_tasks_category_tasks_success(user_repo, category_repo, task_repo, solve_repo, regular_user, test_category):
    """GET /category/{category_name}, Успех: Успешное получение задач по категории"""
    uc = CategoryTasksUseCase(category_repo, task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, category_name="OSINT")
    assert result.category.name == "OSINT"


def test_tasks_category_tasks_not_found(user_repo, category_repo, task_repo, solve_repo, regular_user):
    """GET /category/{category_name}, Логическая ошибка: категория не существует"""
    uc = CategoryTasksUseCase(category_repo, task_repo, solve_repo)
    with pytest.raises(NotFoundError):
        uc.execute(user_id=regular_user.id, category_name="NON_EXISTENT")


def test_tasks_task_detail_success(user_repo, category_repo, task_repo, solve_repo, regular_user, test_category, test_task):
    """GET /<category>/<task>, Успех: Успешное получение деталей задачи с проверкой описания и ссылок"""
    uc = TaskDetailUseCase(category_repo, task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, category_name="OSINT", task_name="Анонимный спортсмен")
    assert result.task.title == "Анонимный спортсмен"
    assert result.solved is False


def test_tasks_task_detail_wrong_category(user_repo, category_repo, task_repo, solve_repo, regular_user, test_category):
    """GET /<category>/<task>, Логическая ошибка: поиск задачи в неправильной категории"""
    other_category = Category(id=0, name="WEB")
    other_category = category_repo.add(other_category)
    flag_hash = bcrypt.hashpw(b"flag", bcrypt.gensalt()).decode("utf-8")
    task = Task(id=0, title="Task1", description="Desc", flag_hash=flag_hash, points=100, category_id=test_category.id)
    task_repo.add(task)
    uc = TaskDetailUseCase(category_repo, task_repo, solve_repo)
    with pytest.raises(NotFoundError):
        uc.execute(user_id=regular_user.id, category_name="WEB", task_name="Task1")


# ============== ТЕСТЫ: SUBMIT FLAG ==============

def test_submit_flag_success(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /submit-flag, Успех: Успешная отправка правильного флага"""
    uc = SubmitFlagUseCase(task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, flag="seculeti{test_flag_123}")
    assert result.success is True
    assert result.points == 1000


def test_submit_flag_wrong_flag(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /submit-flag, Логическая ошибка: отправка неправильного флага"""
    uc = SubmitFlagUseCase(task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, flag="seculeti{wrong}")
    assert result.success is False
    assert result.message == "Неверный флаг"


def test_submit_flag_already_solved(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /submit-flag, Логическая ошибка: повторная отправка флага для решенной задачи"""
    uc = SubmitFlagUseCase(task_repo, solve_repo)
    uc.execute(user_id=regular_user.id, flag="seculeti{test_flag_123}")
    result = uc.execute(user_id=regular_user.id, flag="seculeti{test_flag_123}")
    assert result.success is False
    assert result.message == "Уже решено"


def test_submit_flag_empty_flag(user_repo, task_repo, solve_repo, regular_user):
    """POST /submit-flag, Логическая ошибка: отправка пустого флага"""
    uc = SubmitFlagUseCase(task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, flag="")
    assert result.success is False


# ============== ТЕСТЫ: LEADERBOARD ==============

def test_leaderboard_success(user_repo, task_repo, solve_repo, regular_user, test_task):
    """GET /api/leaderboard, Успешное получение рейтинга после решения задачи"""
    solve = Solve(id=0, user_id=regular_user.id, task_id=test_task.id,
                  solved_at=datetime.now(timezone.utc), points_awarded=1000, is_forfeit=False)
    solve_repo.add(solve)
    uc = LeaderboardUseCase(user_repo, task_repo, solve_repo)
    result = uc.execute()
    assert len(result.players) >= 1
    assert result.total_tasks >= 1


def test_leaderboard_empty(user_repo, task_repo, solve_repo):
    """GET /api/leaderboard, Логическая ошибка: получение рейтинга когда нет задач и решений возвращает пустой список игроков"""
    uc = LeaderboardUseCase(user_repo, task_repo, solve_repo)
    result = uc.execute()
    assert isinstance(result.players, list)
    assert result.total_tasks >= 0


# ============== ТЕСТЫ: SUGGESTIONS ==============

def test_suggest_list_success(user_repo, proposal_repo, category_repo, regular_user, test_category):
    """GET /suggests, Успешное получение списка предложений пользователя"""
    from datetime import datetime
    from app.domain.entities import Proposal
    proposal = Proposal(id=0, user_id=regular_user.id, title="New Task", description="Desc",
                        category_id=test_category.id, difficulty="medium", points=100,
                        flag="flag", hints="", status="pending", created_at=datetime.now(timezone.utc))
    proposal_repo.add(proposal)
    uc = ListSuggestionsUseCase(proposal_repo, category_repo)
    result = uc.execute(user_id=regular_user.id)
    assert len(result.proposals) >= 1


def test_suggest_list_empty(user_repo, proposal_repo, category_repo, regular_user):
    """GET /suggest, Логическая ошибка: Получение списка когда нет предложений возвращает пустой список"""
    uc = ListSuggestionsUseCase(proposal_repo, category_repo)
    result = uc.execute(user_id=regular_user.id)
    assert len(result.proposals) == 0


def test_suggest_submit_success(user_repo, proposal_repo, task_repo, regular_user, test_category):
    """POST /suggest/submit, Успех: Успешное создание предложения задачи со статусом pending"""
    uc = SubmitSuggestionUseCase(proposal_repo, task_repo)
    proposal = uc.execute(user_id=regular_user.id, title="My Task", category_id=test_category.id,
                          description="My Description", points=150, flag="seculeti{flag}",
                          hints="hint", difficulty="hard")
    assert proposal.title == "My Task"
    assert proposal.status == "pending"


def test_suggest_submit_duplicate_title(user_repo, proposal_repo, task_repo, regular_user, test_category):
    """POST /suggest/submit, Логическая ошибка: создание предложения с дублирующимся названием"""
    uc = SubmitSuggestionUseCase(proposal_repo, task_repo)
    uc.execute(user_id=regular_user.id, title="My Task", category_id=test_category.id,
               description="Desc", points=100, flag="flag")
    with pytest.raises(DuplicateError):
        uc.execute(user_id=regular_user.id, title="My Task", category_id=test_category.id,
                   description="Desc", points=100, flag="flag")


def test_suggest_submit_validation_error(user_repo, proposal_repo, task_repo, regular_user):
    """POST /suggest/submit, Логическая ошибка: создание предложения с пустыми полями"""
    uc = SubmitSuggestionUseCase(proposal_repo, task_repo)
    with pytest.raises(ValidationError):
        uc.execute(user_id=regular_user.id, title="", category_id=0, description="", points=0, flag="")


# ============== ТЕСТЫ: FORFEIT TASK ==============

def test_forfeit_task_success(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /tasks/<id>/forfeit, Успех: Успешный отказ от баллов для просмотра райтапов"""
    uc = ForfeitTaskUseCase(task_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, task_id=test_task.id)
    assert result.status == "created"
    solve = solve_repo.get_by_user_task(regular_user.id, test_task.id)
    assert solve.is_forfeit is True
    assert solve.points_awarded == 0


def test_forfeit_task_already_forfeit(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /tasks/<id>/forfeit, Логическая ошибка: повторный отказ от баллов"""
    uc = ForfeitTaskUseCase(task_repo, solve_repo)
    uc.execute(user_id=regular_user.id, task_id=test_task.id)
    result = uc.execute(user_id=regular_user.id, task_id=test_task.id)
    assert result.status == "already_forfeit"


def test_forfeit_task_already_solved(user_repo, task_repo, solve_repo, regular_user, test_task):
    """POST /tasks/<id>/forfeit, Логическая ошибка: Отказ от баллов после решения задачи возвращает статус already_solved"""
    submit_uc = SubmitFlagUseCase(task_repo, solve_repo)
    submit_uc.execute(user_id=regular_user.id, flag="seculeti{test_flag_123}")
    forfeit_uc = ForfeitTaskUseCase(task_repo, solve_repo)
    result = forfeit_uc.execute(user_id=regular_user.id, task_id=test_task.id)
    assert result.status == "already_solved"


# ============== ТЕСТЫ: WRITEUPS ==============

def test_writeups_list_success(user_repo, task_repo, solve_repo, writeup_repo, regular_user, test_task):
    """GET /writeups, Успех: Получение списка райтапов для решенной задачи"""
    solve = Solve(id=0, user_id=regular_user.id, task_id=test_task.id,
                  solved_at=datetime.now(timezone.utc), points_awarded=1000, is_forfeit=False)
    solve_repo.add(solve)
    from app.domain.entities import Writeup
    writeup = Writeup(id=0, user_id=regular_user.id, task_id=test_task.id,
                      content="This is a writeup", created_at=datetime.now(timezone.utc))
    writeup_repo.add(writeup)
    uc = ListWriteupsUseCase(writeup_repo, task_repo, user_repo, solve_repo)
    result = uc.execute(user_id=regular_user.id, task_id=None)
    assert len(result.writeups) >= 1


def test_writeups_list_no_access(user_repo, task_repo, solve_repo, writeup_repo, regular_user, test_task):
    """GET /writeups, Логическая ошибка: попытка получить райтапы для нерешенной задачи"""
    uc = ListWriteupsUseCase(writeup_repo, task_repo, user_repo, solve_repo)
    with pytest.raises(ValidationError):
        uc.execute(user_id=regular_user.id, task_id=test_task.id)


def test_writeups_submit_success(user_repo, task_repo, solve_repo, writeup_repo, regular_user, test_task):
    """POST /writeups/submit, Успех: Успешная публикация райтапа для решенной задачи"""
    solve = Solve(id=0, user_id=regular_user.id, task_id=test_task.id,
                  solved_at=datetime.now(timezone.utc), points_awarded=1000, is_forfeit=False)
    solve_repo.add(solve)
    uc = SubmitWriteupUseCase(writeup_repo, solve_repo)
    writeup = uc.execute(user_id=regular_user.id, task_id=test_task.id, content="My solution")
    assert writeup.content == "My solution"


def test_writeups_submit_not_solved(user_repo, task_repo, solve_repo, writeup_repo, regular_user, test_task):
    """POST /writeups/submit, Логическая ошибка: публикация райтапа для нерешенной задачи"""
    uc = SubmitWriteupUseCase(writeup_repo, solve_repo)
    with pytest.raises(ValidationError):
        uc.execute(user_id=regular_user.id, task_id=test_task.id, content="My solution")


def test_writeups_submit_duplicate(user_repo, task_repo, solve_repo, writeup_repo, regular_user, test_task):
    """POST /writeups/submit, Логическая ошибка: повторная публикация райтапа для той же задачи"""
    solve = Solve(id=0, user_id=regular_user.id, task_id=test_task.id,
                  solved_at=datetime.now(timezone.utc), points_awarded=1000, is_forfeit=False)
    solve_repo.add(solve)
    uc = SubmitWriteupUseCase(writeup_repo, solve_repo)
    uc.execute(user_id=regular_user.id, task_id=test_task.id, content="First")
    with pytest.raises(DuplicateError):
        uc.execute(user_id=regular_user.id, task_id=test_task.id, content="Second")


# ============== ТЕСТЫ: ADMIN ==============

def test_admin_dashboard_success(user_repo, task_repo, proposal_repo, admin_user, test_task):
    """GET /admin, Успех: Успешное получение дашборда администратора"""
    uc = AdminDashboardUseCase(user_repo, task_repo, proposal_repo)
    result = uc.execute()
    assert result.user_count >= 1
    assert result.task_count >= 1


def test_admin_tasks_list_success(task_repo, category_repo):
    """GET /admin/tasks, Успех: Успешное получение списка задач для администрирования"""
    uc = AdminTasksUseCase(task_repo, category_repo)
    result = uc.execute()
    assert hasattr(result, 'tasks')
    assert hasattr(result, 'categories')


def test_admin_add_task_success(task_repo, test_category):
    """GET /admin/tasks/add, Успех: Успешное добавление новой задачи админом"""
    uc = AdminAddTaskUseCase(task_repo)
    task = uc.execute(title="New Admin Task", category_id=test_category.id,
                      description="Description", points=200, flag="seculeti{admin_flag}")
    assert task.title == "New Admin Task"
    assert task.points == 200


def test_admin_add_task_duplicate_error(task_repo, test_category, test_task):
    """POST /admin/tasks/add, Логическая ошибка: добавление задачи с существующим названием"""
    uc = AdminAddTaskUseCase(task_repo)
    with pytest.raises(DuplicateError):
        uc.execute(title=test_task.title, category_id=test_category.id,
                   description="Desc", points=100, flag="flag")


def test_admin_add_task_validation_error(task_repo):
    """POST /admin/tasks/add,Логическая ошибка: добавление задачи с пустыми полями"""
    uc = AdminAddTaskUseCase(task_repo)
    with pytest.raises(ValidationError):
        uc.execute(title="", category_id=0, description="", points=0, flag="")


def test_admin_edit_task_success(task_repo, test_task):
    """POST /admin/tasks/<id>/edit,Успешное редактирование задачи"""
    uc = AdminEditTaskUseCase(task_repo)
    updated = uc.execute(task_id=test_task.id, title="Updated Title",
                         category_id=test_task.category_id, description="Updated Desc",
                         points=500, flag=None)
    assert updated.title == "Updated Title"
    assert updated.points == 500


def test_admin_edit_task_not_found(task_repo):
    """POST /admin/tasks/<id>/edit,Логическая ошибка: редактирование несуществующей задачи"""
    uc = AdminEditTaskUseCase(task_repo)
    with pytest.raises(NotFoundError):
        uc.execute(task_id=9999, title="Title", category_id=1, description="Desc", points=100, flag=None)


def test_admin_delete_task_success(task_repo, solve_repo, writeup_repo, test_task):
    """POST /admin/tasks/<id>/delete, Успешное удаление задачи"""
    uc = AdminDeleteTaskUseCase(task_repo, solve_repo, writeup_repo)
    uc.execute(task_id=test_task.id, confirm="yes")
    assert task_repo.get_by_id(test_task.id) is None


def test_admin_delete_task_no_confirm(task_repo, solve_repo, writeup_repo, test_task):
    """POST /admin/tasks/<id>/delete,Логическая ошибка: удаление без подтверждения"""
    uc = AdminDeleteTaskUseCase(task_repo, solve_repo, writeup_repo)
    uc.execute(task_id=test_task.id, confirm="")
    assert task_repo.get_by_id(test_task.id) is not None


def test_admin_delete_task_not_found(task_repo, solve_repo, writeup_repo):
    """ POST /admin/tasks/<id>/delete, Логическая ошибка: удаление несуществующей задачи"""
    uc = AdminDeleteTaskUseCase(task_repo, solve_repo, writeup_repo)
    with pytest.raises(NotFoundError):
        uc.execute(task_id=9999, confirm="yes")


def test_admin_proposals_list_success(proposal_repo, category_repo, regular_user, test_category):
    """GET /admin/proposals: Успешное получение списка ожидающих предложений"""
    from datetime import datetime
    from app.domain.entities import Proposal
    proposal = Proposal(id=0, user_id=regular_user.id, title="Pending Task", description="Desc",
                        category_id=test_category.id, difficulty="medium", points=100,
                        flag="flag", hints="", status="pending", created_at=datetime.now(timezone.utc))
    proposal_repo.add(proposal)
    uc = AdminProposalsUseCase(proposal_repo, category_repo)
    result = uc.execute()
    assert len(result.proposals) >= 1


def test_admin_approve_proposal_success(proposal_repo, task_repo, regular_user, test_category):
    """POST /admin/suggest/<id>/approve: Успешное одобрение предложения и создание задачи"""
    from datetime import datetime
    from app.domain.entities import Proposal
    proposal = Proposal(id=0, user_id=regular_user.id, title="Approved Task", description="Desc",
                        category_id=test_category.id, difficulty="medium", points=100,
                        flag="seculeti{approved}", hints="", status="pending", created_at=datetime.now(timezone.utc))
    proposal_repo.add(proposal)
    uc = AdminApproveProposalUseCase(proposal_repo, task_repo)
    task = uc.execute(proposal_id=proposal.id)
    assert task.title == "Approved Task"
    updated = proposal_repo.get_by_id(proposal.id)
    assert updated.status == "approved"


def test_admin_approve_proposal_not_found(proposal_repo, task_repo):
    """POST /admin/suggest/<id>/approve, Логическая ошибка: одобрение несуществующего предложения"""
    uc = AdminApproveProposalUseCase(proposal_repo, task_repo)
    with pytest.raises(NotFoundError):
        uc.execute(proposal_id=9999)


def test_admin_reject_proposal_success(proposal_repo, regular_user, test_category):
    """POST /admin/suggest/<id>/reject: Успешное отклонение предложения"""
    from datetime import datetime
    from app.domain.entities import Proposal
    proposal = Proposal(id=0, user_id=regular_user.id, title="Rejected Task", description="Desc",
                        category_id=test_category.id, difficulty="medium", points=100,
                        flag="flag", hints="", status="pending", created_at=datetime.now(timezone.utc))
    proposal_repo.add(proposal)
    uc = AdminRejectProposalUseCase(proposal_repo)
    rejected = uc.execute(proposal_id=proposal.id)
    assert rejected.status == "rejected"


def test_admin_reject_proposal_not_found(proposal_repo):
    """POST /admin/suggest/<id>/reject, Логическая ошибка: отклонение несуществующего предложения"""
    uc = AdminRejectProposalUseCase(proposal_repo)
    with pytest.raises(NotFoundError):
        uc.execute(proposal_id=9999)