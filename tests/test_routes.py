# tests/test_routes.py

from werkzeug.security import generate_password_hash
from kouteihyo_app.models import db, Company, User


def test_home_page(client):
    # 未ログイン時はログインページへリダイレクトされる
    resp = client.get("/", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "ログイン" in html


def test_login_logout_flow(client, app):
    # テスト用に会社とユーザーを作成
    with app.app_context():
        c = Company(name="ログイン社")
        db.session.add(c)
        db.session.commit()
        u = User(
            company_id=c.id,
            display_name="ログ太郎",
            email="login@test.jp",
            password_hash=generate_password_hash("password"),
            role="company"
        )
        db.session.add(u)
        db.session.commit()

    # ログイン処理（カレンダー画面へリダイレクト）
    resp = client.post(
        "/login",
        data={"email": "login@test.jp", "password": "password"},
        follow_redirects=True
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "カレンダー" in html

    # ログアウト処理（再びログインページへ）
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "ログイン" in html
