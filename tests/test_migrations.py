# tests/test_migrations.py

import os
import pytest
from alembic import command
from alembic.config import Config
from kouteihyo_app.app import app

@pytest.fixture
def alembic_cfg(tmp_path):
    ini_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'migrations', 'alembic.ini')
    )
    cfg = Config(ini_path)
    # In-memory SQLite を使用
    cfg.set_main_option('sqlalchemy.url', 'sqlite:///:memory:')
    # migrations ディレクトリを指定
    migrations_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'migrations')
    )
    cfg.set_main_option('script_location', migrations_path)
    return cfg


def test_migrations_apply(alembic_cfg):
    # 最新マイグレーションを問題なく適用できることを確認
    with app.app_context():
        command.upgrade(alembic_cfg, 'head')