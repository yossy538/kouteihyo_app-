# test_admin_user.py

import pytest
from flask import url_for
from kouteihyo_app.models import User, Company, db
from werkzeug.security import generate_password_hash, check_password_hash

@pytest.fixture
def admin_user(app):
    with app.app_context():
        company = Company(name="管理者会社")
        db.session.add(company)
        db.session.commit()
        user = User(
            company_id=company.id,
            username="adminuser",
            display_name="管理者",
            email="admin@example.com",
            password_hash=generate_password_hash("AdminPass123"),
            role="admin",
            must_change_password=False
        )
        db.session.add(user)
        db.session.commit()
        yield user

def test_admin_create_user_page_access(client, admin_user):
    # 管理者でログイン
    client.post(url_for('main.login'), data={
        'username': 'adminuser',
        'password': 'AdminPass123'
    }, follow_redirects=True)
    response = client.get(url_for('main.admin_create_user'))
    assert response.status_code == 200
    assert "ユーザー作成" in response.data.decode("utf-8")

def test_admin_create_user_success(client, admin_user, app):
    # 管理者でログイン
    client.post(url_for('main.login'), data={
        'username': 'adminuser',
        'password': 'AdminPass123'
    }, follow_redirects=True)
    with app.app_context():
        company = Company.query.first()
    data = {
        'company_id': company.id,
        'display_name': 'テストユーザー',
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'TestPass123',
        'role': 'company',
        'submit': 'アカウント作成'
    }
    response = client.post(url_for('main.admin_create_user'), data=data, follow_redirects=True)
    assert response.status_code == 200
    assert 'ユーザーを作成しました' in response.data.decode('utf-8')
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.display_name == 'テストユーザー'
        assert user.email == 'testuser@example.com'
        assert user.company_id == company.id
        assert user.role == 'company'
        assert check_password_hash(user.password_hash, 'TestPass123')

def test_admin_create_user_duplicate_username(client, admin_user, app):
    # 管理者でログイン
    client.post(url_for('main.login'), data={
        'username': 'adminuser',
        'password': 'AdminPass123'
    }, follow_redirects=True)
    with app.app_context():
        existing_user = User.query.first()
    data = {
        'company_id': existing_user.company_id,
        'display_name': '重複ユーザー',
        'username': existing_user.username,  # 重複 username
        'email': 'newemail@example.com',
        'password': 'TestPass123',
        'role': 'company',
        'submit': 'アカウント作成'
    }
    response = client.post(url_for('main.admin_create_user'), data=data)
    assert 'このユーザー名は既に使われています' in response.data.decode('utf-8')
