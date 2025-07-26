# tests/test_routes.py

import pytest
from werkzeug.security import generate_password_hash
from kouteihyo_app.models import db, Company, User

# --- ユーザー作成ヘルパー ---
def create_user_with_company(app, username, password, role="company"):
    with app.app_context():
        c = Company(name=f"{username}_社")
        db.session.add(c)
        db.session.commit()
        u = User(
            company_id=c.id,
            display_name=f"{username}_太郎",
            email=f"{username}@test.jp",
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(u)
        db.session.commit()
        print("★User.query.all() =", User.query.all())  # ここ追加

        return u, c

# --- ログインヘルパー ---
def login(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=True  # ←この部分を「False」に！
    )

# --- テスト用ユーザー大量生成 ---
@pytest.fixture
def test_users(app):
    user_info = [
        {"username": "user1", "pw": "pass1234"},
        {"username": "user2", "pw": "start5678"},
        {"username": "user3", "pw": "hello8901"},
    ]
    with app.app_context():
        c = Company(name="複数ユーザー社")
        db.session.add(c)
        db.session.commit()
        users = []
        for info in user_info:
            u = User(
                company_id=c.id,
                display_name=info["username"],
                email=f"{info['username']}@test.jp",
                username=info["username"],
                password_hash=generate_password_hash(info["pw"]),
                role="company"
            )
            db.session.add(u)
            users.append(u)
        db.session.commit()
        return users, user_info

# --- テスト本体 ---
def test_login_logout_flow(client, app):
    u, _ = create_user_with_company(app, "loginuser", "password")
    resp = login(client, "loginuser", "password")
    print("=== LOGIN RESPONSE ===")
    print("Status:", resp.status)
    print("Headers:", dict(resp.headers))
    print("Body:", resp.get_data(as_text=True)[:800])  # 長ければ先頭だけ

    # デバッグ: ログイン後のレスポンス内容確認
    if "カレンダー" not in resp.get_data(as_text=True):
        print("★『カレンダー』が見つからなかった！")
        if "ログイン" in resp.get_data(as_text=True):
            print("★実はログイン画面に戻されている！")
        if "<title>Redirecting" in resp.get_data(as_text=True):
            print("★リダイレクトHTMLになってる！Location:", resp.headers.get("Location"))

    assert "カレンダー" in resp.get_data(as_text=True)
    resp = client.get("/logout", follow_redirects=True)
    print("=== LOGOUT RESPONSE ===")
    print("Status:", resp.status)
    print("Headers:", dict(resp.headers))
    print("Body:", resp.get_data(as_text=True)[:800])

    assert "ログイン" in resp.get_data(as_text=True)






def test_login_failure(client, app):
    create_user_with_company(app, "failuser", "password")
    resp = client.post(
        "/login",
        data={"username": "failuser", "password": "wrongpass"},
        follow_redirects=True
    )
    print("LOGIN HTML:", resp.get_data(as_text=True))
    assert "ユーザー名またはパスワードが違います" in resp.get_data(as_text=True)


def test_password_change_flow(client, app):
    u, _ = create_user_with_company(app, "passtaro", "oldpass123")
    login(client, "passtaro", "oldpass123")

    # 成功
    resp = client.post(
        "/password_change",
        data={
            "old_password": "oldpass123",
            "new_password": "newpass456",
            "new_password2": "newpass456"
        },
        follow_redirects=True
    )
    assert "パスワードを変更しました" in resp.get_data(as_text=True)
    # 新パスでOK
    client.get("/logout", follow_redirects=True)
    resp = login(client, "passtaro", "newpass456")
    assert "カレンダー" in resp.get_data(as_text=True)
    # 旧パスはNG
    client.get("/logout", follow_redirects=True)
    resp = login(client, "passtaro", "oldpass123")
    assert "ユーザー名またはパスワードが違います" in resp.get_data(as_text=True)

    # エラーケース
    login(client, "passtaro", "newpass456")
    # 現在パス誤り
    resp = client.post("/password_change",
        data={
            "old_password": "mismatch",
            "new_password": "xxxxxxxy",
            "new_password2": "xxxxxxxy"
        },
        follow_redirects=True
    )
    assert "現在のパスワードが違います" in resp.get_data(as_text=True)
    # 新パス不一致
    resp = client.post("/password_change",
        data={
            "old_password": "newpass456",
            "new_password": "shortpass",
            "new_password2": "different"
        },
        follow_redirects=True
    )
    assert "新しいパスワードが一致しません" in resp.get_data(as_text=True)
    # 新パス短すぎ
    resp = client.post("/password_change",
        data={
            "old_password": "newpass456",
            "new_password": "short",
            "new_password2": "short"
        },
        follow_redirects=True
    )
    assert "パスワードは8文字以上にしてください" in resp.get_data(as_text=True)

def test_schedule_list_requires_login(client):
    resp = client.get("/schedules", follow_redirects=True)
    assert "ログイン" in resp.get_data(as_text=True)

def test_admin_menu_visible_only_for_admin(client, app):
    u, _ = create_user_with_company(app, "adminuser", "password", role="admin")
    login(client, "adminuser", "password")
    resp = client.get("/schedules", follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert "管理者メニュー" in html

def test_company_user_cannot_see_admin_menu(client, app):
    u, _ = create_user_with_company(app, "normaluser", "password", role="company")
    login(client, "normaluser", "password")
    resp = client.get("/schedules", follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert "管理者メニュー" not in html

def test_all_users_can_change_password(client, app, test_users):
    users, user_info = test_users
    for idx, info in enumerate(user_info):
        login(client, info["username"], info["pw"])
        resp = client.post(
            "/password_change",
            data={
                "old_password": info["pw"],
                "new_password": f"newpw{idx}5678",
                "new_password2": f"newpw{idx}5678",
            },
            follow_redirects=True
        )
        assert "パスワードを変更しました" in resp.get_data(as_text=True)
        client.get("/logout", follow_redirects=True)
        resp2 = login(client, info["username"], f"newpw{idx}5678")
        assert "カレンダー" in resp2.get_data(as_text=True)
        client.get("/logout", follow_redirects=True)
        resp3 = login(client, info["username"], info["pw"])
        assert "ユーザー名またはパスワードが違います" in resp3.get_data(as_text=True)
