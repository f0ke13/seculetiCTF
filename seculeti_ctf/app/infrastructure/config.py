import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    TEMPLATES_AUTO_RELOAD = True
    DB_HOST = os.environ.get("DB_HOST", "db")
    DB_NAME = os.environ.get("DB_NAME", "etuctf")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "11111111")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    @classmethod
    def db_url(cls) -> str:
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        return (
            f"postgresql+psycopg2://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )
