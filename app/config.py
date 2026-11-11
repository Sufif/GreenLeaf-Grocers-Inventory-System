import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'greenleaf-secret-key-change-in-production-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "data" / "greenleaf.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / 'data'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ITEMS_PER_PAGE = 20
    LOW_STOCK_THRESHOLD_DAYS = 15  # for near expiry
