import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///datavision.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORAGE_ROOT = BASE_DIR / "storage" / "projects"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    @classmethod
    def validate(cls):
        if cls.APP_ENV == "production" and cls.SECRET_KEY in {"", "dev-secret", "change-me-in-production"}:
            raise RuntimeError("Defina uma SECRET_KEY segura antes de iniciar em producao.")
