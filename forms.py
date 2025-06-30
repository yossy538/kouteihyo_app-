# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from wtforms import SelectField, TextAreaField


class LoginForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')
    
class ScheduleForm(FlaskForm):
    time_slot = SelectField(
        '時間帯',
        choices=[('午前', '午前'), ('午後', '午後'), ('終日', '終日'), ('夜', '夜')],
        validators=[DataRequired()]
    )
    task_name = StringField('作業名', validators=[DataRequired()])
    person_in_charge = StringField('担当者', validators=[DataRequired()])
    comment = TextAreaField('コメント')
    submit = SubmitField('更新する')
