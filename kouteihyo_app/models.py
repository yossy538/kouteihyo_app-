# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# ── トップレベルは必ず行頭から ──
db = SQLAlchemy()

class Company(db.Model):
    __tablename__ = 'companies'
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    users     = db.relationship('User',     backref='company',  lazy=True)
    schedules = db.relationship('Schedule', backref='company', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    display_name  = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    username      = db.Column(db.String(64), unique=True, nullable=False)   # ←追加済み！
    password_hash = db.Column(db.String(128), nullable=False)
    role          = db.Column(db.String(20), nullable=False)  # 'admin' or 'company'
    must_change_password = db.Column(db.Boolean, nullable=False, default=True)  # ←これを追加！！


    created_schedules = db.relationship(
        'Schedule',
        foreign_keys='Schedule.created_by',
        backref='creator',
        lazy=True
    )
    site_notes = db.relationship('SiteNote', backref='creator', lazy=True)
    date_notes = db.relationship('DateNote', backref='creator', lazy=True)


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id               = db.Column(db.Integer, primary_key=True)
    site_name        = db.Column(db.String(255), nullable=False)
    date             = db.Column(db.Date, nullable=False)
    end_date         = db.Column(db.Date, nullable=True)
    time_slot        = db.Column(db.String(10), nullable=False)
    task_name        = db.Column(db.String(100), nullable=False)
    person_in_charge = db.Column(db.String(100))
    comment          = db.Column(db.Text)
    client_person    = db.Column(db.String(100))
    client_comment   = db.Column(db.String(255))

    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

class SiteNote(db.Model):
    __tablename__ = 'site_notes'

    id         = db.Column(db.Integer, primary_key=True)
    site_name  = db.Column(db.String(255), unique=True, nullable=False)
    note       = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class DateNote(db.Model):
    __tablename__ = 'date_notes'

    id             = db.Column(db.Integer, primary_key=True)
    date           = db.Column(db.Date, nullable=False, unique=True)
    client_person  = db.Column(db.String(255), nullable=True)
    client_comment = db.Column(db.Text, nullable=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

