import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_migrate import Migrate
from dotenv import load_dotenv

# モデル・ルート・設定はパッケージ相対インポート
from kouteihyo_app.models import db, User, SiteNote
from kouteihyo_app.routes import bp
from kouteihyo_app.config import DevelopmentConfig, ProductionConfig

# 環境変数を読み込む（.env）
load_dotenv()
IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'

app = Flask(__name__)
# 設定ファイル適用
app.config.from_object(ProductionConfig if IS_PRODUCTION else DevelopmentConfig)

# ── SQLite の DB ファイルを絶対パス指定 ──
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, 'instance')
# instance フォルダがなければ作成
os.makedirs(instance_dir, exist_ok=True)
db_file = os.path.join(instance_dir, 'kouteihyo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_file}"

# セキュリティ設定（Talisman）
SELF = "'self'"
CDN = "https://cdn.jsdelivr.net"

if IS_PRODUCTION:
    Talisman(
        app,
        content_security_policy={
            'default-src': SELF,
            'script-src': [SELF, CDN],
            'style-src': [SELF, CDN],
            'img-src': '*',
            'font-src': '*',
        },
        content_security_policy_report_only=True,
        content_security_policy_report_uri='/csp-report',
        frame_options='DENY',
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True
    )
else:
    Talisman(
        app,
        content_security_policy={
            'default-src': SELF,
            'script-src': [SELF, CDN, "'unsafe-inline'"],
            'style-src': [SELF, CDN, "'unsafe-inline'"],
            'img-src': '*',
            'font-src': '*',
        },
        content_security_policy_report_only=False,
        frame_options=None,
        strict_transport_security=False
    )

# DB 初期化 & マイグレーション
db.init_app(app)
migrate = Migrate(app, db)

# ログイン管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprint 登録
app.register_blueprint(bp)

# エラーハンドラー
def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

register_error_handlers(app)

# 実行
if __name__ == '__main__':
    app.run(debug=not IS_PRODUCTION, host='127.0.0.1', port=5010)
