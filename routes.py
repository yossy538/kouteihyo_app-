# routes.py（前半と末尾はそのままでOK）

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Schedule
from forms import LoginForm
from collections import defaultdict
from datetime import date
from flask import jsonify
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Schedule
from datetime import datetime
from werkzeug.security import check_password_hash




bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return '工程表アプリへようこそ！'

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            print('✅ ログイン成功：リダイレクトします')
            return redirect(url_for('main.schedule_calendar'))
        flash('メールアドレスまたはパスワードが違います')
    else:
        print('❌ バリデーションエラー:', form.errors)

    return render_template('login.html', form=form)



@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/schedules')
@login_required
def schedule_list():
    from models import Schedule

    if current_user.role == 'admin':
        schedules = Schedule.query.order_by(Schedule.date.asc()).all()
    else:
        schedules = Schedule.query.filter_by(company_id=current_user.id).order_by(Schedule.date.asc()).all()

    # 日付ごとにまとめる
    schedules_by_date = defaultdict(list)
    for s in schedules:
        schedules_by_date[s.date.strftime('%Y-%m-%d')].append(s)

    return render_template('schedule/list.html', schedules_by_date=schedules_by_date)

@bp.route('/schedules/calendar')
@login_required
def schedule_calendar():
    return render_template('schedule/calendar.html')

@bp.route('/api/schedules')
@login_required
def api_schedules():
    from models import Schedule

    # ✅ 全ユーザーに全予定を表示（ログインしていればOK）
    schedules = Schedule.query.all()

    # 会社IDごとの色マップ（5色まで）
    company_colors = {
        1: '#ff9999',  # 三空工業（赤）
        2: '#99ccff',  # サトワ電工（青）
        3: '#99ff99',  # 平和住建（緑）
        4: '#ffff99',  # 浅野ダクト（黄）
        5: '#cc99ff',  # 菱輝金型（紫）
    }

    events = []
    for s in schedules:
       events.append({
    "id": s.id, 
    "title": f"{s.time_slot} {s.task_name}",
    "start": s.date.isoformat(),
    "color": company_colors.get(s.company_id, '#cccccc'),  # 背景色
    "textColor": "#000000"  # ←ここを '#ffffff' にすると白文字、見やすくなる
})

    return jsonify(events)

@bp.route('/schedules/<int:id>', methods=['GET', 'POST'])
@login_required
def schedule_detail(id):
    schedule = Schedule.query.get_or_404(id)

    if request.method == 'POST':
        if current_user.id == schedule.company_id:
            schedule.time_slot = request.form.get('time_slot')
            schedule.task_name = request.form.get('task_name')
            schedule.person_in_charge = request.form.get('person_in_charge')
            schedule.comment = request.form.get('comment')
            db.session.commit()
            flash('予定を更新しました')
            return redirect(url_for('main.schedule_calendar'))
        else:
            flash('編集権限がありません')
            return redirect(url_for('main.schedule_detail', id=id))

    return render_template('schedule/detail.html', schedule=schedule)

@bp.route('/schedules/date/<date_str>', methods=['GET', 'POST'])
@login_required
def schedule_by_date(date_str):
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('日付の形式が不正です')
        return redirect(url_for('main.schedule_calendar'))

    schedules = Schedule.query.filter_by(date=selected_date).all()

    if request.method == 'POST':
        for s in schedules:
            if s.company_id == current_user.id:
                s.time_slot = request.form.get(f'time_slot_{s.id}')
                s.task_name = request.form.get(f'task_name_{s.id}')
                s.person_in_charge = request.form.get(f'person_in_charge_{s.id}')
                s.comment = request.form.get(f'comment_{s.id}')

            if current_user.company_name == s.company.company_name:
                s.client_person = request.form.get(f'client_person_{s.id}')
                s.client_comment = request.form.get(f'client_comment_{s.id}')

        db.session.commit()
        flash('予定を更新しました')
        return redirect(url_for('main.schedule_calendar'))

    return render_template('schedule/by_date.html', schedules=schedules, selected_date=selected_date)


@bp.route('/schedules/add/<date>', methods=['POST'])
@login_required
def schedule_add(date):
    selected_date = datetime.strptime(date, "%Y-%m-%d").date()

    new_schedule = Schedule(
        site_name=request.form.get('site_name'),  # ✅ これを追加！
        date=selected_date,
        company_id=current_user.id,
        time_slot=request.form.get('time_slot'),
        task_name=request.form.get('task_name'),
        person_in_charge=request.form.get('person_in_charge'),
        comment=request.form.get('comment'),
        client_person=request.form.get('client_person'),   # ← 今後の拡張もOK
        client_comment=request.form.get('client_comment'),
        created_by=current_user.id
    )

    db.session.add(new_schedule)
    db.session.commit()

    return redirect(url_for('main.schedule_by_date', date_str=date))

