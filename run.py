# run.py
from dotenv import load_dotenv
load_dotenv()

import os
from kouteihyo_app import create_app

app = create_app()

# ---------------------------------------------------------
# ① 自動マイグレーション（本番のみ）
# ---------------------------------------------------------
if os.environ.get("IS_PRODUCTION", "").lower() == "true":
    from flask_migrate import upgrade
    with app.app_context():
        print("🔄 Running database migrations...")
        upgrade()
        print("✅ Migration complete!")

# ---------------------------------------------------------
# ② アプリ起動（ローカルデバッグ用）
# ---------------------------------------------------------
if __name__ == "__main__":
    print("[DEBUG] os.getcwd() =", os.getcwd())
    print("[DEBUG] SECRET_KEY(環境変数) =", os.environ.get("SECRET_KEY"))
    app.run(debug=True, port=5010)


