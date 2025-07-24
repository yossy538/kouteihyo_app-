# app.py

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from models import db, User, SiteNote
from routes import bp
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv
import os

# ✅ 環境変数を読み込む（.env）
load_dotenv()
IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'

app = Flask(__name__)
app.config.from_object(ProductionConfig if IS_PRODUCTION else DevelopmentConfig)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kouteihyo.db'

# ✅ セキュリティ設定（Talisman）
SELF = "'self'"
CDN = "https://cdn.jsdelivr.net"

if IS_PRODUCTION:
    # 🔒 本番用のセキュリティ
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
    # 🛠 ローカル用の緩め設定
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

# DBやログイン周りの設定
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(bp)

# エラーハンドラー
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500

# 実行
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=not IS_PRODUCTION, host='127.0.0.1', port=5010)


