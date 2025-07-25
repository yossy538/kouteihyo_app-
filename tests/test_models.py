# tests/test_models.py

import datetime
from kouteihyo_app.models import db, Company, User, Schedule

def test_company_user_schedule_crud(app):
    # ── Company CRUD ──
    c = Company(name="テスト社")
    db.session.add(c)
    db.session.commit()
    assert c.id is not None

    # ── User CRUD ──
    u = User(
        company_id=c.id,
        display_name="テスト太郎",
        email="taro@test.jp",
        password_hash="hogehoge",
        role="company"
    )
    db.session.add(u)
    db.session.commit()
    assert u.id is not None
    # backref で company が参照できる
    assert u.company == c

    # ── Schedule CRUD ──
    s = Schedule(
        site_name="現場A",
        date=datetime.date(2025, 8, 1),
        time_slot="午前",
        task_name="作業1",
        company_id=c.id,
        created_by=u.id
    )
    db.session.add(s)
    db.session.commit()
    assert s.id is not None
    # backref で creator と company が参照できる
    assert s.creator == u
    assert s.company == c

    # ── Update ──
    s.task_name = "作業2"
    db.session.commit()
    assert Schedule.query.get(s.id).task_name == "作業2"

    # ── Delete ──
    db.session.delete(s)
    db.session.delete(u)
    db.session.delete(c)
    db.session.commit()
    assert Company.query.get(c.id) is None
