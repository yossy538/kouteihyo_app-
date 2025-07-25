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
from kouteihyo_app.config import DevelopmentConfig, ProductionConfig

load_dotenv()
IS_PRODUCTION = os.getenv('IS_PRODUCTION', 'false').lower() == 'true'

print("TEMPLATE FOLDER PATH:", os.path.join(os.path.dirname(__file__), '..', 'templates'))
print("STATIC FOLDER PATH:", os.path.join(os.path.dirname(__file__), '..', 'static'))


app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "hogehoge_dev_key")


basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, '..', 'instance')
os.makedirs(instance_dir, exist_ok=True)
db_file = os.path.join(instance_dir, 'kouteihyo.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_file}"

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

# DB, Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
