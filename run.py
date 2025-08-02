# run.py
from dotenv import load_dotenv
load_dotenv()

import os
from kouteihyo_app import create_app

app = create_app()

# ---------------------------------------------------------
# ① 自動マイグレーション（IS_PRODUCTION が true の時だけ）
# ---------------------------------------------------------
if os.environ.get("IS_PRODUCTION", "").lower() == "true":
    from flask_migrate import upgrade
    with app.app_context():
        print("🔄 Running database migrations...")
        upgrade()
        print("✅ Migration complete!")

# ---------------------------------------------------------
# ② 必要なら初期ユーザー自動投入
# ---------------------------------------------------------
from kouteihyo_app.models import db, User, Company
from werkzeug.security import generate_password_hash

def create_initial_users(app):
    with app.app_context():
        if User.query.first():
            print("ℹ️ ユーザーは既に存在します。初期投入スキップ。")
            return

        companies = {c.name: c for c in Company.query.all()}
        user_data = [
            ('mitsubayashi', '三空工業'),
            ('saniihara', '三空工業'),
            ('sanyoshida', '三空工業'),
            ('satowatanabe', 'サトワ電工'),
            ('satoohashi', 'サトワ電工'),
            ('satouser3', 'サトワ電工'),
            ('heiwakoike1', '平和住建'),
            ('heiwakoike2', '平和住建'),
            ('ryokiyoshida', '菱輝金型工業'),
            ('ryokimiyaguchi', '菱輝金型工業'),
            ('aoikondo', '葵ツール'),
            ('aoiasano', '葵ツール'),
        ]

        for username, company_name in user_data:
            if not User.query.filter_by(username=username).first():
                if company_name not in companies:
                    print(f"⚠️ 会社 {company_name} が存在しません。スキップ。")
                    continue

                user = User(
                    username=username,
                    display_name=username,
                    email=f"{username}@example.com",
                    password_hash=generate_password_hash('pass1234'),
                    company_id=companies[company_name].id,
                    role='company'
                )
                db.session.add(user)

        db.session.commit()
        print("✅ ユーザー一括登録完了！")

# ---------------------------------------------------------
# ③ フラグで初期ユーザー登録をON/OFF
# ---------------------------------------------------------
if os.environ.get("INIT_USERS_ON_STARTUP", "").lower() == "true":
    create_initial_users(app)

# ---------------------------------------------------------
# ④ アプリ起動（ローカル用）
# ---------------------------------------------------------
if __name__ == "__main__":
    print("[DEBUG] os.getcwd() =", os.getcwd())
    print("[DEBUG] SECRET_KEY(環境変数) =", os.environ.get("SECRET_KEY"))
    app.run(debug=True, port=5010)
