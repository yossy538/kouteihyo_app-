# kouteihyo_app/forms.py


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from werkzeug.security import check_password_hash
import re


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('現在のパスワード', validators=[DataRequired()])
    new_password = PasswordField('新しいパスワード', validators=[DataRequired()])
    confirm_password = PasswordField('確認用パスワード', validators=[DataRequired(), EqualTo('new_password')])

    def __init__(self, current_user_password_hash, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user_password_hash = current_user_password_hash

    def validate_new_password(self, field):
        password = field.data

        if check_password_hash(self.current_user_password_hash, password):
            raise ValidationError("新しいパスワードは現在のパスワードと異なる必要があります。")

        if len(password) < 8:
            raise ValidationError("パスワードは8文字以上にしてください。")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("大文字を1文字以上含めてください。")
        if not re.search(r'[a-z]', password):
            raise ValidationError("小文字を1文字以上含めてください。")
        if not re.search(r'[0-9]', password):
            raise ValidationError("数字を1文字以上含めてください。")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise ValidationError("記号（!@#$%^&*()など）を含めてください。")
# ログインフォーム（ユーザー名ログイン方式）
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

# 管理者用ユーザー作成フォーム（必要フィールドをすべて記載）
class AdminUserCreateForm(FlaskForm):
    company_id   = SelectField('会社', coerce=int, validators=[DataRequired()])
    display_name = StringField('表示名', validators=[DataRequired(), Length(max=100)])
    username     = StringField('ユーザー名', validators=[
        DataRequired(), Length(max=64),
        Regexp(r'^[a-zA-Z0-9_]+$', message="半角英数字・アンダースコアのみ")
    ])
    email        = StringField('メールアドレス', validators=[DataRequired(), Email(), Length(max=100)])
    password     = PasswordField('初期パスワード', validators=[
        DataRequired(),
        Length(min=8, max=100, message='8文字以上で入力してください'),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$', message='英字と数字の両方を含めてください')
    ])
    role         = SelectField('ロール', choices=[('company', '協力会社'), ('admin', '管理者')], validators=[DataRequired()])
    submit       = SubmitField('アカウント作成')

# スケジュール用フォーム（そのまま使うならOK）
class ScheduleForm(FlaskForm):
    time_slot        = SelectField('時間帯', choices=[('午前', '午前'), ('午後', '午後'), ('終日', '終日'), ('夜', '夜')], validators=[DataRequired()])
    task_name        = StringField('作業名', validators=[DataRequired(), Length(max=100)])
    person_in_charge = StringField('担当者', validators=[DataRequired(), Length(max=100)])
    comment          = TextAreaField('コメント', validators=[Length(max=500)])
    submit           = SubmitField('更新する')

# 削除フォーム
class DeleteNoteForm(FlaskForm):
    submit = SubmitField('削除する')
