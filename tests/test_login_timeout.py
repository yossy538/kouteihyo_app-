# test_login_timeout.py

import pytest
from flask import session
from kouteihyo_app import create_app, db
from kouteihyo_app.models import User
from werkzeug.security import generate_password_hash
from datetime import timedelta

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=2)  # テスト時は超短縮
    with app.app_context():
        db.create_all()
        user = User(username="testuser", email="test@example.com", password_hash=generate_password_hash("testpass"), company_id=1, role="company", display_name="test")
        db.session.add(user)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()

def login(client):
    return client.post("/login", data={"username": "testuser", "password": "testpass"}, follow_redirects=True)

def test_login_timeout(app):
    client = app.test_client()

    response = login(client)
    html = response.data.decode("utf-8")
    # ログイン直後はログイン画面ではないので、login-formは出ないはず
    assert 'id="login-form"' not in html

    with client.session_transaction() as sess:
        assert "_user_id" in sess

    import time
    time.sleep(3)

    # セッション切れ後、認証必須ページにアクセス
    response = client.get("/schedules/calendar", follow_redirects=True)
    html = response.data.decode("utf-8")
    # タイムアウト後はログイン画面（login-form）が出てくる
    assert 'id="login-form"' in html
