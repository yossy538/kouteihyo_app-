# run.py
from dotenv import load_dotenv
load_dotenv()  # ←本当にここで最初に呼ぶ！

import os
from kouteihyo_app import create_app

app = create_app()

if __name__ == "__main__":
    print("[DEBUG] os.getcwd() =", os.getcwd())
    print("[DEBUG] SECRET_KEY(環境変数) =", os.environ.get("SECRET_KEY"))
    app.run(debug=True, port=5010)
