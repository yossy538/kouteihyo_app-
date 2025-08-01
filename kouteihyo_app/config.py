import os
import secrets
from datetime import timedelta 

class Config:
    # ← ここにデフォルト値（"dev-secret-key"）は絶対入れない！
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///local.db")  # 本番は環境変数必須
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Cookie/セッションの本番推奨設定
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    # セッション有効期限
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=120)

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"  # ローカル用

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    # SESSION_COOKIE_SECURE/REMEMBER_COOKIE_SECUREなどはConfigの値を継承
    # 必ず環境変数で上書きする前提

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SECRET_KEY = "test-key"
    SERVER_NAME = "localhost.localdomain"
