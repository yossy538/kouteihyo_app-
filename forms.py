# kouteihyo_app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Regexp

class LoginForm(FlaskForm):
    email = StringField(
        'メールアドレス',
        validators=[DataRequired(), Email(), Length(max=100)]
    )
    password = PasswordField(
        'パスワード',
        validators=[DataRequired()]  # 必要に応じて Length(min=8) を追加
    )
    submit = SubmitField('ログイン')


class AdminUserCreateForm(FlaskForm):
    """管理者専用：ユーザー作成フォーム"""
    # 会社選択は既存の company テーブルからプルダウンにする想定
    company_id   = SelectField('会社', coerce=int, validators=[DataRequired()])
    display_name = StringField(
        '表示名',
        validators=[DataRequired(), Length(max=100)]
    )
    email        = StringField(
        'メールアドレス',
        validators=[DataRequired(), Email(), Length(max=100)]
    )
    password     = PasswordField(
        '初期パスワード',
        validators=[
            DataRequired(),
            Length(min=8, max=100, message='8文字以上で入力してください'),
            Regexp(
                r'^(?=.*[A-Za-z])(?=.*\d).+$',
                message='英字と数字の両方を含めてください'
            )
        ]
    )
    role = SelectField(
        'ロール',
        choices=[('company', '協力会社'), ('admin', '管理者')],
        validators=[DataRequired()]
    )
    submit = SubmitField('アカウント作成')


class ScheduleForm(FlaskForm):
    """スケジュール登録／編集フォーム"""
    time_slot        = SelectField(
        '時間帯',
        choices=[('午前', '午前'), ('午後', '午後'), ('終日', '終日'), ('夜', '夜')],
        validators=[DataRequired()]
    )
    task_name        = StringField(
        '作業名',
        validators=[DataRequired(), Length(max=100)]
    )
    person_in_charge = StringField(
        '担当者',
        validators=[DataRequired(), Length(max=100)]
    )
    comment          = TextAreaField(
        'コメント',
        validators=[Length(max=500)]
    )
    submit           = SubmitField('更新する')
