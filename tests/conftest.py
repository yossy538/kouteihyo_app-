# tests/conftest.py

import os
import sys

# ─── プロジェクトルートをモジュール探索パスに追加 ───
# tests ディレクトリの二つ上（sankuu_Projects）を先頭に
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root)

import pytest
# パッケージ名付きインポート
from kouteihyo_app.app import app as flask_app, db

@pytest.fixture
def app():
    # テスト用設定
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
