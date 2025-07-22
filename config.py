import os
import secrets

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # 🔐 セッションとCookie保護設定（本番想定）
    SESSION_COOKIE_SECURE = True            # HTTPSのみ送信（本番はTrue）
    SESSION_COOKIE_HTTPONLY = True          # JSからアクセス不可
    SESSION_COOKIE_SAMESITE = 'Lax'         # クロスサイト制限
    REMEMBER_COOKIE_SECURE = True           # remember meもHTTPSのみ
    REMEMBER_COOKIE_HTTPONLY = True         # remember meもJSから見えない


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False           # ローカルではFalseでOK
    REMEMBER_COOKIE_SECURE = False          # 同上


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    # 本番では全てTrue（Configから継承済み）
