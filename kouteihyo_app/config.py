# config.py
import os
import secrets
from datetime import timedelta 

class Config:
    # SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)  本番はこっち
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"  # ← 開発中はこれでもOK

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # 🔐 セッションとCookie保護設定（本番想定）
    SESSION_COOKIE_SECURE = True            # HTTPSのみ送信（本番はTrue）
    SESSION_COOKIE_HTTPONLY = True          # JSからアクセス不可
    SESSION_COOKIE_SAMESITE = 'Lax'         # クロスサイト制限
    REMEMBER_COOKIE_SECURE = True           # remember meもHTTPSのみ
    REMEMBER_COOKIE_HTTPONLY = True         # remember meもJSから見えない

  # ✅ セッション有効期限の設定（ステップ10）
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=120)  # 120分で自動ログアウト
class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False           # ローカルではFalseでOK
    REMEMBER_COOKIE_SECURE = False          # 同上


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    # 本番では全てTrue（Configから継承済み）

# config.py
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'   # ← 'None' や False ではなく 'Lax' で固定推奨
    REMEMBER_COOKIE_SECURE = False
    SECRET_KEY = "test-key"
    SERVER_NAME = "localhost.localdomain"  # ←これも追加
