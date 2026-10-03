import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///datavision.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORAGE_ROOT = BASE_DIR / "storage" / "projects"
