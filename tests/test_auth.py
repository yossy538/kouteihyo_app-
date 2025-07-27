# test_auth.py

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

from kouteihyo_app.models import db, User

@pytest.fixture
def user_with_force_change(app):
    # テスト用ユーザー（must_change_password=True）
    user = User(
        company_id=1,
        display_name="テストユーザー",
        username="testuser",
        email="testuser@example.com",
        password_hash=generate_password_hash("initpass123"),
        role="company",
        must_change_password=True
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_force_password_change_redirect(client, user_with_force_change):
    # ログインPOST
    response = client.post(
        url_for('main.login'),
        data={
            "username": "testuser",
            "password": "initpass123"
        },
        follow_redirects=False
    )
    # 強制パスワード変更画面にリダイレクトされるか
    assert response.status_code == 302
    assert "/force_password_change" in response.headers["Location"]

def test_password_change_turns_off_flag(client, app, user_with_force_change):
    # まずログインしてセッション確保
    client.post(
        url_for('main.login'),
        data={"username": "testuser", "password": "initpass123"},
        follow_redirects=True
    )
    # 強制パスワード変更
    response = client.post(
        url_for('main.force_password_change'),
        data={
            "old_password": "initpass123",
            "new_password": "newpass456",
            "new_password2": "newpass456"
        },
        follow_redirects=True
    )
    # 成功メッセージが表示されているか
    assert "パスワードが変更されました" in response.data.decode("utf-8")


    # DB側のフラグもFalseになっているか
    user = User.query.filter_by(username="testuser").first()
    assert user.must_change_password is False

    # 再度ログインすると通常ページへ遷移するか
    client.get(url_for('main.logout'))
    response2 = client.post(
        url_for('main.login'),
        data={"username": "testuser", "password": "newpass456"},
        follow_redirects=False
    )
    assert response2.status_code == 302
    assert "/schedule_calendar" in response2.headers["Location"] or "/schedules/calendar" in response2.headers["Location"]

@pytest.fixture
def user_without_force_change(app):
    user = User(
        company_id=1,
        display_name="通常ユーザー",
        username="user2",
        email="user2@example.com",
        password_hash=generate_password_hash("regularpass123"),
        role="company",
        must_change_password=False
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_normal_login_redirects_to_dashboard(client, user_without_force_change):
    response = client.post(
        url_for('main.login'),
        data={
            "username": "user2",
            "password": "regularpass123"
        },
        follow_redirects=False
    )
    assert response.status_code == 302
    assert "/schedule_calendar" in response.headers["Location"] or "/schedules/calendar" in response.headers["Location"]
