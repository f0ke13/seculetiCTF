import sys
from pathlib import Path

# Добавляем путь к проекту
root = Path(__file__).resolve().parent.parent.parent  # папка seculeti_ctf
sys.path.insert(0, str(root))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

# Импортируем нужные модели и функции из проекта
from app.infrastructure.db import Base, build_db, init_db, Database
from app.infrastructure.config import Config
from app.infrastructure.di import build_container
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
    
    # Создаем контейнер с тестовой сессией
    container = build_container()
    
    # Подменяем сессию в репозиториях на тестовую
    # (это зависит от реализации, упрощенный вариант)
    
    with app.app_context():
        # Инициализируем тестовые данные
        _seed_test_data(db_session)
        db_session.commit()
    
    yield app.test_client()


def _seed_test_data(session):
    """Добавляем тестовые данные"""
    from app.infrastructure.db import UserModel, CategoryModel, TaskModel
    import bcrypt
    
    # Создаем админа
    admin = session.query(UserModel).filter_by(username="admin").first()
    if not admin:
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        admin = UserModel(username="admin", password=hashed, role="admin")
        session.add(admin)
        session.flush()
    
    # Создаем категорию
    cat = session.query(CategoryModel).filter_by(name="Beginner").first()
    if not cat:
        cat = CategoryModel(name="Beginner")
        session.add(cat)
        session.flush()
    
    # Создаем задачу
    task = session.query(TaskModel).filter_by(title="Без комментариев").first()
    if not task:
        flag_hash = bcrypt.hashpw(b"seculeti{Plz_D0nt_C0mm3nt_th1$}", bcrypt.gensalt()).decode("utf-8")
        task = TaskModel(
            title="Без комментариев",
            description="Тестовое задание",
            flag_hash=flag_hash,
            points=15,
            category_id=cat.id
        )
        session.add(task)