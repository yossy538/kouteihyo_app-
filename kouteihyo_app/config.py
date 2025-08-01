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

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True

    # 明示的に本番用セキュリティ設定を再掲
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    # 本番で環境変数がなければエラーにする
    if not os.environ.get("SECRET_KEY"):
        raise ValueError("SECRET_KEY is not set for production!")
    if not os.environ.get("DATABASE_URL"):
        raise ValueError("DATABASE_URL is not set for production!")

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"  # ローカル用

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SECRET_KEY = "test-key"
    SERVER_NAME = "localhost.localdomain"
