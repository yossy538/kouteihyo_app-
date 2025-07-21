from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email

# ここを必ず一番上か、LoginForm より前に追加してください
class DeleteNoteForm(FlaskForm):
    """日付メモ削除用のダミーフォーム"""
    pass

class LoginForm(FlaskForm):
    """ログインフォーム"""
    email = StringField(
        'メールアドレス',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'パスワード',
        validators=[DataRequired()]
    )
    submit = SubmitField('ログイン')

class AdminUserCreateForm(FlaskForm):
    """管理者専用：ユーザー作成フォーム"""
    company_name = StringField(
        '会社名',
        validators=[DataRequired()]
    )
    email = StringField(
        'メールアドレス',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        '初期パスワード',
        validators=[DataRequired()]
    )
    role = SelectField(
        'ロール',
        choices=[('company', '協力会社'), ('admin', '管理者')],
        validators=[DataRequired()]
    )
    submit = SubmitField('アカウント作成')

class ScheduleForm(FlaskForm):
    """スケジュール登録／編集フォーム"""
    time_slot = SelectField(
        '時間帯',
        choices=[('午前', '午前'), ('午後', '午後'), ('終日', '終日'), ('夜', '夜')],
        validators=[DataRequired()]
    )
    task_name = StringField(
        '作業名',
        validators=[DataRequired()]
    )
    person_in_charge = StringField(
        '担当者',
        validators=[DataRequired()]
    )
    comment = TextAreaField('コメント')
    submit = SubmitField('更新する')
