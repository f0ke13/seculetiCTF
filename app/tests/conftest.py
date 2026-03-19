import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

TEST_DB_URI = 'postgresql://postgres:11111111@localhost:5432/etuctf_test'

def create_test_db():
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='11111111',
        port='5432',
        dbname='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'etuctf_test'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE etuctf_test")
    cur.close()
    conn.close()

# Подменяем URI ДО импорта app, чтобы SQLAlchemy не успел подключиться к db
import os
os.environ['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URI

from main import app, db

@pytest.fixture(scope='session')
def client():
    create_test_db()

    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URI

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()      # закрываем сессии перед drop
        db.drop_all()