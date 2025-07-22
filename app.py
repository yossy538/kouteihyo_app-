# app.py

from flask import Flask, render_template  # ← render_template を追加
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_talisman import Talisman
from models import db, User, SiteNote
from routes import bp
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv
import os

load_dotenv()   

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kouteihyo.db'

Talisman(app, content_security_policy=None)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(bp)

# ✅ エラーハンドラーを追加
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500

# ✅ サーバー起動
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("SECRET_KEY:", app.config['SECRET_KEY'])
    print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
        
    app.run(debug=True, host='127.0.0.1', port=5010)


