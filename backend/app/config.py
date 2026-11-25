# filepath: backend/app/config.py
import os
import secrets
import sys
import shutil
from datetime import timedelta

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    DATA_DIR = os.getenv('INVENTORY_DATA_DIR', os.path.join(os.environ.get('PROGRAMDATA', r'C:\ProgramData'), 'NewWayInventory'))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.getenv('INVENTORY_DATA_DIR', os.path.abspath(os.path.join(BASE_DIR, '..', 'instance')))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'inventory.db')
if getattr(sys, 'frozen', False) and not os.path.exists(DB_PATH):
    legacy_db = os.path.join(BASE_DIR, 'inventory.db')
    if os.path.isfile(legacy_db):
        shutil.copy2(legacy_db, DB_PATH)

APP_ENV = os.getenv('APP_ENV', 'production').lower()
IS_PRODUCTION = APP_ENV == 'production'


def _secret(name):
    value = os.getenv(name)
    if IS_PRODUCTION and (not value or len(value) < 32):
        raise RuntimeError(f'{name} must be set to a random value of at least 32 characters in production')
    return value or secrets.token_urlsafe(48)


class Config:
    SECRET_KEY = _secret('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = _secret('JWT_SECRET_KEY')
    CORS_ORIGINS = [origin.strip() for origin in os.getenv(
        'CORS_ORIGINS', 'http://localhost:5173' if not IS_PRODUCTION else ''
    ).split(',') if origin.strip()]
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    JWT_COOKIE_SECURE = IS_PRODUCTION
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_ACCESS_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    JWT_REFRESH_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME or '')
    MAIL_SUPPRESS_SEND = not bool(MAIL_USERNAME and MAIL_PASSWORD)
    SMTP_CREDENTIAL_ENCRYPTION_KEY = os.getenv('SMTP_CREDENTIAL_ENCRYPTION_KEY')
    TRUST_PROXY = IS_PRODUCTION
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
