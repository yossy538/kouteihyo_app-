# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'company'

    schedules = db.relationship('Schedule', backref='company', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)  # 開始日
    end_date = db.Column(db.Date, nullable=True)  # 終了日
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)  # 午前／午後／夜
    task_name = db.Column(db.String(100), nullable=False)
    person_in_charge = db.Column(db.String(100))  # 担当者
    comment = db.Column(db.Text)


    company_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.Column(db.Integer)  # ログインユーザーのID

    client_person = db.Column(db.String(100))   # 依頼元の担当者
    client_comment = db.Column(db.String(255))  # 依頼元からの伝言や要望など
    
class SiteNote(db.Model):
    __tablename__ = 'site_notes'

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), unique=True, nullable=False)  # 現場名
    note = db.Column(db.Text, nullable=True)  # 注意事項本文
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 作成ユーザー

# models.py
class DateNote(db.Model):
    __tablename__ = 'date_notes'
    id             = db.Column(db.Integer, primary_key=True)
    date           = db.Column(db.Date, nullable=False, unique=True)
    client_person  = db.Column(db.String(255), nullable=True)
    client_comment = db.Column(db.Text,    nullable=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
