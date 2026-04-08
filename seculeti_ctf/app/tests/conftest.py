import sys
from pathlib import Path

# === КРИТИЧНО ВАЖНО ДЛЯ РАБОТЫ ===
root = Path(__file__).resolve().parent.parent.parent  # папка seculeti_ctf
sys.path.insert(0, str(root))

print(f"✅ PYTHONPATH установлен: {root}")

# Теперь импорты будут работать
from app.infrastructure.flask_app import create_app
from app.infrastructure.db import db, Base
from app.domain.entities import User, Category, Task

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, scoped_session


TEST_DATABASE_URI = "postgresql://postgres:11111111@db_test:5432/etuctf_test"


@pytest.fixture(scope="session")
def test_db_engine():
    from sqlalchemy import create_engine
    engine = create_engine(TEST_DATABASE_URI, echo=False)
    yield engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_db_engine):
    with test_db_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.commit()
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
    app = create_app(testing=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
    db.init_app(app)

    with app.app_context():
        _seed_test_data()
        db.session.commit()

    yield app.test_client()


def _seed_test_data():
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", role="admin")
        db.session.add(admin)

    if not Category.query.filter_by(name="Beginner").first():
        cat = Category(name="Beginner")
        db.session.add(cat)
        db.session.flush()

        task = Task(
            title="Без комментариев",
            description="Тестовое задание",
            flag_hash="$2b$12$dummyhash123456789",
            points=15,
            category_id=cat.id
        )
        db.session.add(task)