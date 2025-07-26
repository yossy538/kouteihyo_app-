# confitest.py
# conftest.py
import pytest
from kouteihyo_app import create_app, db
from kouteihyo_app.config import TestingConfig

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        # ←ここに追加！
        print("APP SECRET_KEY:", app.config["SECRET_KEY"])
        print("APP TESTING:", app.config.get("TESTING"))
        print("APP SERVER_NAME:", app.config.get("SERVER_NAME"))
        print("WTF_CSRF_ENABLED (from config):", app.config["WTF_CSRF_ENABLED"])  # ←これを追加
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
