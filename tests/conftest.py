# conftest.py
import pytest
from kouteihyo_app import create_app, db
from kouteihyo_app.config import TestingConfig

@pytest.fixture
def app():
    app = create_app(config_class=TestingConfig)
    print("【TEST: DB URI】", app.config["SQLALCHEMY_DATABASE_URI"])  # ←必ずここで出す
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
