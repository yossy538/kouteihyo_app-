# tests/test_models.py

import datetime
from kouteihyo_app.models import db, Company, User, Schedule, SiteNote, DateNote

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
        username="taro",
        password_hash="hogehoge",
        role="company"
    )
    db.session.add(u)
    db.session.commit()
    assert u.id is not None
    assert u.company == c
    assert u.username == "taro"

    # ── Schedule CRUD ──
    s = Schedule(
        site_name="現場A",
        date=datetime.date(2025, 8, 1),
        time_slot="午前",
        task_name="作業1",
        company_id=c.id,
        created_by=u.id,
        person_in_charge="現場責任者A"
    )
    db.session.add(s)
    db.session.commit()
    assert s.id is not None
    assert s.creator == u
    assert s.company == c

    # created_schedulesリレーションの確認
    assert s in u.created_schedules

    # ── SiteNote CRUD ──
    site_note = SiteNote(
        site_name="現場A",
        note="現場メモ",
        created_by=u.id
    )
    db.session.add(site_note)
    db.session.commit()
    assert site_note.id is not None
    assert site_note.creator == u
    assert site_note.site_name == "現場A"

    # ── DateNote CRUD ──
    date_note = DateNote(
        date=datetime.date(2025, 8, 1),
        client_person="依頼元担当",
        client_comment="日付メモ",
        created_by=u.id
    )
    db.session.add(date_note)
    db.session.commit()
    assert date_note.id is not None
    assert date_note.creator == u
    assert date_note.client_person == "依頼元担当"

    # ── Update ──
    s.task_name = "作業2"
    db.session.commit()
    assert Schedule.query.get(s.id).task_name == "作業2"

    # ── Delete（逆順で安全に） ──
    db.session.delete(date_note)
    db.session.delete(site_note)
    db.session.delete(s)
    db.session.delete(u)
    db.session.delete(c)
    db.session.commit()
    assert Company.query.get(c.id) is None
