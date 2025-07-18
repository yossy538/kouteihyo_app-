# app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User, SiteNote
from routes import bp  # Blueprint を routes.py に書く前提
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 本番では環境変数で管理
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kouteihyo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False  # ⚠️ 開発用。公開前に True に戻す！


# DB初期化
db.init_app(app)

migrate = Migrate(app, db)

# Login管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'  

# ログインユーザーの取得方法
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Blueprint登録（routes.py に書く）
app.register_blueprint(bp)

# サーバー起動
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 最初だけDB作成（migrate不要なら）
app.run(debug=True, host='127.0.0.1', port=5010)