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
    response = client.post(
        url_for('main.login'),
        data={
            "username": "testuser",
            "password": "initpass123"
        },
        follow_redirects=False
    )
    assert response.status_code == 302
    assert "/force_password_change" in response.headers["Location"]

def test_password_change_turns_off_flag(client, app, user_with_force_change):
    # まずログインしてセッション確保
    client.post(
        url_for('main.login'),
        data={"username": "testuser", "password": "initpass123"},
        follow_redirects=True
    )
    # 強制パスワード変更POST（リダイレクトは追わない）
    response = client.post(
        url_for('main.force_password_change'),
        data={
            "old_password": "initpass123",
            "new_password": "Abcd1234!",
            "new_password2": "Abcd1234!"
        },
        follow_redirects=False
    )
    # 実際どこにリダイレクトされるか確認
    assert response.status_code == 302
    assert "/schedules/calendar" in response.headers["Location"] or "/schedule_calendar" in response.headers["Location"]

    # そのリダイレクト先でflashを拾う
    response2 = client.get(response.headers["Location"], follow_redirects=True)
    assert "パスワードが変更されました" in response2.data.decode("utf-8")

    # DB側のフラグもFalseになっているか
    user = User.query.filter_by(username="testuser").first()
    assert user.must_change_password is False

    # 再度ログインすると通常ページへ遷移するか
    client.get(url_for('main.logout'))
    response2 = client.post(
        url_for('main.login'),
        data={"username": "testuser", "password": "Abcd1234!"},
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

@pytest.fixture
def admin_user(app):
    user = User(
        company_id=1,
        display_name="管理者",
        username="admin",
        email="admin@example.com",
        password_hash=generate_password_hash("password"),
        role="admin",
        must_change_password=False
    )
    db.session.add(user)
    db.session.commit()
    yield user

def test_login(client, admin_user):
    response = client.post(url_for('main.login'), data={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 200 or response.status_code == 302
