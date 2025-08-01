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
            role=role,
            must_change_password=False   # ←最初からFalse！
        )
        db.session.add(u)
        db.session.commit()
        return u.id, c.id




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
# tests/test_routes.py

def test_login_logout_flow(client, app):
    u, _ = create_user_with_company(app, "loginuser", "password")
    resp = login(client, "loginuser", "password")
    html = resp.get_data(as_text=True)
    print("=== LOGIN RESPONSE ===")
    print("Status:", resp.status)
    print("Headers:", dict(resp.headers))
    print("Body:", html[:800])

    # ここで判定！
    if 'id="calendar-page"' in html:
        pass
    elif 'id="password-change-form"' in html:
        pass
    else:
        assert False, "カレンダーでもパスワード変更画面でもない"

    # ログアウト判定もIDで
    resp = client.get("/logout", follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert 'id="login-form"' in html

def test_by_date_page_visible_after_login(client, app):
    user_id, company_id = create_user_with_company(app, "dateuser", "password")
    from kouteihyo_app.models import Schedule, User, db
    from datetime import date as dt_date
    with app.app_context():
        s = Schedule(
            company_id=company_id,
            created_by=user_id,
            site_name="テスト現場",
            date=dt_date(2025, 8, 1),
            end_date=None,
            time_slot="午前",
            task_name="テスト作業",
            person_in_charge="太郎",
            comment="テストコメント"
        )
        db.session.add(s)
        # パスワード変更フラグをFalseに
        u = User.query.get(user_id)
        u.must_change_password = False
        db.session.commit()

    login(client, "dateuser", "password")
    # ↓ ここを修正
    resp = client.get("/schedules/date/2025-08-01", follow_redirects=True)
    html = resp.get_data(as_text=True)
    print(html)  # ←ここに追加！assertの前
    assert 'id="by-date-page"' in html
    assert 'id="date-note-form"' in html or 'id="bulk-edit-form"' in html

    # 2回目も同様に修正
    login(client, "dateuser", "password")
    resp = client.get("/schedules/date/2025-08-01", follow_redirects=True)
    html = resp.get_data(as_text=True)
    assert 'id="by-date-page"' in html
    assert 'id="date-note-form"' in html or 'id="bulk-edit-form"' in html







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
        # 1. まず旧パスでログイン
        login(client, info["username"], info["pw"])
        # 2. パスワード変更実行
        resp = client.post(
            "/password_change",
            data={
                "old_password": info["pw"],
                "new_password": f"newpw{idx}5678",
                "new_password2": f"newpw{idx}5678",
            },
            follow_redirects=True
        )
        # デバッグ出力
        print("【DEBUG HTML】", resp.get_data(as_text=True))
        # 3. 変更メッセージが本当に表示されるか
        assert "パスワードを変更しました" in resp.get_data(as_text=True)

        # 4. 一度ログアウト
        client.get("/logout", follow_redirects=True)
        # 5. 新パスワードで再ログインできるか
        resp2 = login(client, info["username"], f"newpw{idx}5678")
        assert "カレンダー" in resp2.get_data(as_text=True)
        # 6. もう一度ログアウト
        client.get("/logout", follow_redirects=True)
        # 7. 旧パスワードではログインできない
        resp3 = login(client, info["username"], info["pw"])
        assert "ユーザー名またはパスワードが違います" in resp3.get_data(as_text=True)

def test_force_password_change_redirect(client, app):
    # must_change_password=True なユーザーを追加
    with app.app_context():
        c = Company(name="強制変更社")
        db.session.add(c)
        db.session.commit()
        u = User(
            company_id=c.id,
            display_name="ForceUser",
            email="forceuser@test.jp",
            username="forceuser",
            password_hash=generate_password_hash("pass1234"),
            role="company",
            must_change_password=True  # 🔥 ここが重要
        )
        db.session.add(u)
        db.session.commit()

    resp = client.post("/login", data={
        "username": "forceuser",
        "password": "pass1234"
    }, follow_redirects=True)

    html = resp.get_data(as_text=True)
    assert 'id="password-change-form"' in html or "パスワード変更" in html

import pytest
from kouteihyo_app.routes import is_strong_password

@pytest.mark.parametrize("pw, expected", [
    ("Abcd1234!", True),    # 全部含む
    ("abcd1234!", False),   # 大文字なし
    ("ABCD1234!", False),   # 小文字なし
    ("Abcdabcd!", False),   # 数字なし
    ("Abcd12345", False),   # 記号なし
    ("Abc!1", False),       # 8文字未満
    ("12345678!", False),   # 英字なし
    ("AbcdEFGH!", False),   # 数字なし
    ("Abcd1234!", True),    # ふたたび正常
])
def test_is_strong_password(pw, expected):
    """パスワードが強固かどうか判定関数のテスト"""
    assert is_strong_password(pw) == expected

