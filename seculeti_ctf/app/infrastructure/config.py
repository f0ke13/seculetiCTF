import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    TEMPLATES_AUTO_RELOAD = True
