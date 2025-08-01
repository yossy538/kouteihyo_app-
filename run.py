# run.py
from dotenv import load_dotenv
load_dotenv()

import os
from kouteihyo_app import create_app

app = create_app()

# ★ここで自動マイグレーション
if os.environ.get("IS_PRODUCTION") == "true":
    from flask_migrate import upgrade
    with app.app_context():
        upgrade()

if __name__ == "__main__":
    print("[DEBUG] os.getcwd() =", os.getcwd())
    print("[DEBUG] SECRET_KEY(環境変数) =", os.environ.get("SECRET_KEY"))
    app.run(debug=True, port=5010)
