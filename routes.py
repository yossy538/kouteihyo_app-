# routes.py（前半と末尾はそのままでOK）
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Schedule, DateNote
from forms import LoginForm
from collections import defaultdict
from datetime import date, datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
import jpholiday
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('main.schedule_calendar'))
        flash('メールアドレスまたはパスワードが違います', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/schedules')
@login_required
def schedule_list():
    if current_user.role == 'admin':
        schedules = Schedule.query.order_by(Schedule.date.asc()).all()
    else:
        schedules = Schedule.query.filter_by(company_id=current_user.id).order_by(Schedule.date.asc()).all()

    schedules_by_date = defaultdict(list)
    for s in schedules:
        schedules_by_date[s.date.strftime('%Y-%m-%d')].append(s)

    return render_template('schedule/list.html', schedules_by_date=schedules_by_date)

@bp.route('/schedules/calendar')
@login_required
def schedule_calendar():
    # 今見ている月を渡しておきたい場合は引数化するとさらに便利ですが
    today = datetime.today()
    year, month = today.year, today.month

    # jpholiday で当月の祝日を YYYY-MM-DD 形式で取得
    holidays = [d.strftime('%Y-%m-%d') for d, _ in jpholiday.month_holidays(year, month)]

    return render_template(
        'schedule/calendar.html',
        holiday_list=holidays
    )

@bp.route('/api/schedules')
@login_required
def api_schedules():
    schedules = Schedule.query.all()
    notes     = DateNote.query.all()
    company_colors = {
        1:'#ff9999', 2:'#99ccff', 3:'#99ff99', 4:'#ffff99', 5:'#cc99ff'
    }
    events = []

    # ── 通常のスケジュール ──
    for s in schedules:
        start = s.date
        end   = s.end_date or s.date
        events.append({
            "id":     f"sch-{s.id}",
            "title":  f"{s.time_slot} {s.task_name}",
            "start":  start.isoformat(),
            "end":    (end + timedelta(days=1)).isoformat(),
            "color":  company_colors.get(s.company_id, '#cccccc'),
            "textColor":"#000000",
            "allDay": True,
        })

    # ── 日付メモを背景イベントで追加 ──
    for n in notes:
        events.append({
            "id":        f"memo-{n.id}",
            "title":     "📌 菱輝金型工業様メモ有り",
            "start":     n.date.isoformat(),
            "allDay":    True,
            "color":     "#ffcc00",   # 黄色
            "textColor": "#000000"
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
        flash('編集権限がありません')
    return render_template('schedule/detail.html', schedule=schedule)

@bp.route('/schedules/add', methods=['POST'])
@login_required
def schedule_add():
    date_val = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    end_date_str = request.form.get('end_date')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    new_schedule = Schedule(
        site_name=request.form.get('site_name'),
        date=date_val,
        end_date=end_date,
        company_id=current_user.id,
        time_slot=request.form.get('time_slot'),
        task_name=request.form.get('task_name'),
        person_in_charge=request.form.get('person_in_charge'),
        comment=request.form.get('comment'),
        client_person=request.form.get('client_person'),
        client_comment=request.form.get('client_comment'),
        created_by=current_user.id
    )
    db.session.add(new_schedule)
    db.session.commit()
    return redirect(url_for('main.schedule_by_date', date_str=date_val.strftime('%Y-%m-%d')))

@bp.route('/schedules/delete/<int:id>', methods=['POST'])
@login_required
def schedule_delete(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.company_id != current_user.id:
        flash('自分の会社の予定のみ削除できます。', 'danger')
    else:
        db.session.delete(schedule)
        db.session.commit()
        flash('予定を削除しました。', 'success')
    return redirect(url_for('main.schedule_by_date', date_str=schedule.date.strftime('%Y-%m-%d')))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    from forms import RegisterForm
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('このメールアドレスはすでに登録されています', 'danger')
            return redirect(url_for('main.register'))
        user = User(
            company_name=form.company_name.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='company'
        )
        db.session.add(user)
        db.session.commit()
        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/schedules/client/comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_client_comment(id):
    if current_user.company_name != '菱輝金型工業':
        flash('このページにはアクセスできません。', 'danger')
        return redirect(url_for('main.schedule_by_date', date_str=datetime.today().strftime('%Y-%m-%d')))
    schedule = Schedule.query.get_or_404(id)
    if request.method == 'POST':
        schedule.client_person = request.form.get('client_person')
        schedule.client_comment = request.form.get('client_comment')
        db.session.commit()
        flash('コメントを更新しました。', 'success')
        return redirect(url_for('main.schedule_by_date', date_str=schedule.date.strftime('%Y-%m-%d')))
    return render_template('schedule/client_comment_form.html', schedule=schedule)

@bp.route('/schedules/client/comment/delete/<int:id>', methods=['POST'])
@login_required
def delete_client_comment(id):
    if current_user.company_name != '菱輝金型工業':
        flash('この操作はできません。', 'danger')
        return redirect(url_for('main.schedule_by_date', date_str=datetime.today().strftime('%Y-%m-%d')))
    schedule = Schedule.query.get_or_404(id)
    schedule.client_comment = None
    schedule.client_person = None
    db.session.commit()
    flash('コメントを削除しました。', 'success')
    return redirect(url_for('main.schedule_by_date', date_str=schedule.date.strftime('%Y-%m-%d')))

@bp.route('/schedules/date/<date_str>', methods=['GET','POST'])
@login_required
def schedule_by_date(date_str):
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    schedules     = Schedule.query.filter_by(date=selected_date).all()
    note          = DateNote.query.filter_by(date=selected_date).first()

    if request.method == 'POST':
        # ── ① 作業会社側が編集したとき only ──
        if current_user.company_name != '菱輝金型工業':
            for s in schedules:
                if s.company_id == current_user.id:
                    s.time_slot        = request.form[f'time_slot_{s.id}']
                    s.task_name        = request.form[f'task_name_{s.id}']
                    s.person_in_charge = request.form[f'person_in_charge_{s.id}']
                    s.comment          = request.form[f'comment_{s.id}']

            flash('予定を更新しました', 'success')

        # ── ② 発注元（菱輝金型工業）がコメントだけ編集するとき ──
        else:
            cp = request.form.get('date_client_person')
            cc = request.form.get('date_client_comment')
            if note:
                note.client_person  = cp
                note.client_comment = cc
                flash('メモを更新しました', 'success')
            else:
                new = DateNote(
                    date           = selected_date,
                    client_person  = cp,
                    client_comment = cc,
                    created_by     = current_user.id
                )
                db.session.add(new)
                flash('メモを追加しました', 'success')

        db.session.commit()
        return redirect(url_for('main.schedule_by_date', date_str=date_str))

    return render_template(
        'schedule/by_date.html',
        schedules     = schedules,
        selected_date = selected_date,
        date_note     = note
    )

