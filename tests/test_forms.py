import pytest
from kouteihyo_app import create_app
from kouteihyo_app.forms import ChangePasswordForm
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False  # CSRFを無効化（フォームのテスト用）
    return app

@pytest.fixture
def current_password_hash():
    return generate_password_hash("pass1234")


def test_same_password_not_allowed(app, current_password_hash):
    with app.app_context():
        form = ChangePasswordForm(
            current_user_password_hash=current_password_hash,
            data={
                "old_password": "pass1234",
                "new_password": "pass1234",
                "confirm_password": "pass1234",
            }
        )
        assert not form.validate()
        assert "新しいパスワードは現在のパスワードと異なる必要があります。" in form.new_password.errors


def test_weak_password_too_short(app, current_password_hash):
    with app.app_context():
        form = ChangePasswordForm(
            current_user_password_hash=current_password_hash,
            data={
                "old_password": "pass1234",
                "new_password": "A1!",
                "confirm_password": "A1!",
            }
        )
        assert not form.validate()
        assert "パスワードは8文字以上にしてください。" in form.new_password.errors


def test_missing_uppercase(app, current_password_hash):
    with app.app_context():
        form = ChangePasswordForm(
            current_user_password_hash=current_password_hash,
            data={
                "old_password": "pass1234",
                "new_password": "password1!",
                "confirm_password": "password1!",
            }
        )
        assert not form.validate()
        assert "大文字を1文字以上含めてください。" in form.new_password.errors


def test_valid_password(app, current_password_hash):
    with app.app_context():
        form = ChangePasswordForm(
            current_user_password_hash=current_password_hash,
            data={
                "old_password": "pass1234",
                "new_password": "StrongP@ss1",
                "confirm_password": "StrongP@ss1",
            }
        )
        assert form.validate()
