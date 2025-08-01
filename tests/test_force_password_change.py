import pytest
from werkzeug.security import generate_password_hash
from kouteihyo_app.models import db, User, Company


@pytest.fixture
def user_must_change_password(app):
    """パスワード変更必須ユーザーを作成"""
    with app.app_context():
        company = Company(name="テスト会社")
        db.session.add(company)
        db.session.commit()

        user = User(
            company_id=company.id,
            username="testuser",
            display_name="テストユーザー",
            email="test@example.com",
            password_hash=generate_password_hash("Password123!"),
            must_change_password=True,
            role="company"  # ★ roleを必須指定
        )

        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def logged_in_client(client, user_must_change_password):
    """パスワード変更必須ユーザーでログイン状態にする"""
    client.post(
        "/login",
        data={"username": "testuser", "password": "Password123!"},
        follow_redirects=True
    )
    return client


def test_normal_access_after_change(app, client, user_must_change_password):
    # ① パスワード変更フラグをFalse化
    with app.app_context():
        user_must_change_password.must_change_password = False
        db.session.commit()
        db.session.expire_all()

    # ② セッション完全クリア
    client.get("/logout", follow_redirects=True)
    with client.session_transaction() as sess:
        sess.clear()

    # ③ ログインし直し
    resp = client.post(
        "/login",
        data={"username": "testuser", "password": "Password123!"},
        follow_redirects=True
    )

    # ④ DBから“最新”Userインスタンスで再確認
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        print("【test DEBUG】must_change_password after login:", user.must_change_password)
        assert not user.must_change_password

    # ⑤ 実際の機能ページにもアクセスできるか
    resp = client.get("/schedules", follow_redirects=True)
    print("【TEST】status_code:", resp.status_code)
    assert resp.status_code == 200



