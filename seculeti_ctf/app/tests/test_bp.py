import sys
from pathlib import Path

# Добавляем путь к проекту
root = Path(__file__).resolve().parent.parent.parent  # папка seculeti_ctf
sys.path.insert(0, str(root))

import pytest
import bcrypt
from flask import url_for
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

# Импортируем нужные модели и функции из проекта
from app.infrastructure.db import Base, UserModel, CategoryModel, TaskModel, ProposalModel, SolveModel
from app.infrastructure.flask_app import create_app

TEST_DATABASE_URI = "postgresql://postgres:11111111@localhost:5432/etuctf_test"


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(TEST_DATABASE_URI, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_db_engine):
    # Создаем схему public заново
    with test_db_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    
    # Создаем все таблицы
    Base.metadata.create_all(test_db_engine)
    yield
    Base.metadata.drop_all(test_db_engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    connection = test_db_engine.connect()
    transaction = connection.begin()
    Session = scoped_session(sessionmaker(bind=connection))
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
    app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов
    
    # Подменяем сессию в приложении
    # Это может потребовать адаптации под вашу архитектуру
    if hasattr(app, 'container'):
        # Если используется DI контейнер
        with app.container.db_session.override(db_session):
            client = app.test_client()
            # Сохраняем сессию в клиенте для доступа в тестах
            client.db_session = db_session
            yield client
    else:
        # Упрощенный вариант
        client = app.test_client()
        client.db_session = db_session
        yield client


def _hash_password(password: str) -> str:
    """Хеширование пароля для тестов"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _hash_flag(flag: str) -> str:
    """Хеширование флага для тестов"""
    return bcrypt.hashpw(flag.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# ====================== FIXTURES ДЛЯ ТЕСТОВЫХ ДАННЫХ ======================

@pytest.fixture
def admin_user(db_session):
    """Создает админа для тестов"""
    admin = db_session.query(UserModel).filter_by(username="admin").first()
    if not admin:
        admin = UserModel(
            username="admin",
            password=_hash_password("admin123"),
            role="admin"
        )
        db_session.add(admin)
        db_session.commit()
    return admin


@pytest.fixture
def regular_user(db_session):
    """Создает обычного пользователя для тестов"""
    user = db_session.query(UserModel).filter_by(username="player1").first()
    if not user:
        user = UserModel(
            username="player1",
            password=_hash_password("123"),
            role="user"
        )
        db_session.add(user)
        db_session.commit()
    return user


@pytest.fixture
def admin_client(test_client, admin_user):
    """Клиент с авторизованным админом"""
    test_client.post('/auth/login', data={
        "username": "admin",
        "password": "admin123"
    })
    return test_client


@pytest.fixture
def user_client(test_client, regular_user):
    """Клиент с авторизованным пользователем"""
    test_client.post('/auth/login', data={
        "username": "player1",
        "password": "123"
    })
    return test_client


@pytest.fixture
def test_category(db_session):
    """Создает тестовую категорию"""
    cat = db_session.query(CategoryModel).filter_by(name="OSINT").first()
    if not cat:
        cat = CategoryModel(name="OSINT")
        db_session.add(cat)
        db_session.commit()
    return cat


@pytest.fixture
def test_task(db_session, test_category):
    """Создает тестовое задание"""
    task = db_session.query(TaskModel).filter_by(title="Test OSINT Task").first()
    if not task:
        task = TaskModel(
            title="Test OSINT Task",
            description="Find the gym name",
            points=1000,
            flag_hash=_hash_flag("seculeti{test_flag_2026}"),
            category_id=test_category.id
        )
        db_session.add(task)
        db_session.commit()
    return task


# ====================== ТЕСТЫ АВТОРИЗАЦИИ ======================

def test_register_success(test_client, db_session):
    response = test_client.post('/auth/register', data={
        "username": "newplayer",
        "password": "secret123",
        "confirm_password": "secret123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    response_text = response.get_data(as_text=True)
    assert "Регистрация прошла успешно" in response_text or "успешно" in response_text.lower()
    
    # Проверяем что пользователь создан в БД
    user = db_session.query(UserModel).filter_by(username="newplayer").first()
    assert user is not None
    assert user.role == "user"


def test_register_password_mismatch(test_client):
    response = test_client.post('/auth/register', data={
        "username": "baduser",
        "password": "123",
        "confirm_password": "321"
    })
    assert response.status_code == 200
    assert "Passwords do not match" in response.get_data(as_text=True)


