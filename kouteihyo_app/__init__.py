# kouteihyo_app/__init__.py

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from flask_migrate import Migrate
from dotenv import load_dotenv

from kouteihyo_app.models import db, User, SiteNote
from kouteihyo_app.routes import bp

load_dotenv()

import sys  # ←追加

def create_app(config_class=None):
    IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'
    is_testing = "pytest" in sys.modules

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
    )

    # 1. config_class優先
    if config_class:
        app.config.from_object(config_class)
    # 2. pytest時は自動でTestingConfig
    elif is_testing:
        from .config import TestingConfig
        app.config.from_object(TestingConfig)
    # 3. DATABASE_URL優先
    elif os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    # 4. DB URIがまだ無ければinstance内に自動作成
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(basedir, '..', 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_file = os.path.join(instance_dir, 'kouteihyo.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_file}"

    # SECRET_KEYだけは常にセット
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "hogehoge_dev_key")

    print("==== 現在のDB URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))
    print("=== DEBUG SECRET_KEY ===", app.config['SECRET_KEY'])

    # ...以下省略...


    # --- ここから ---
    SELF = "'self'"
    CDN = "https://cdn.jsdelivr.net"
    if not is_testing:  # ★テスト時は完全スキップ！
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
    # --- ここまで（違いは if not is_testing: でラップするだけ）---

    # DB, Migrate
    db.init_app(app)
    migrate = Migrate(app, db)

    # Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = None


    # ...以下省略...


    @login_manager.user_loader
    def load_user(user_id):
        print("【user_loader CALLED】user_id =", user_id)
        user = User.query.get(int(user_id))
        print("【user_loader returns】", user)
        return user


    # Blueprint
    app.register_blueprint(bp)

    # Error Handlers
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
    return app
