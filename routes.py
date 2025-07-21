from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Schedule, DateNote
from forms import LoginForm
from collections import defaultdict
from datetime import datetime, date, timedelta
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash
import jpholiday 

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
    today = datetime.today()
    year, month = today.year, today.month
    holiday_list = [d.strftime('%Y-%m-%d') for d, _ in jpholiday.month_holidays(year, month)]
    return render_template('schedule/calendar.html', holiday_list=holiday_list)

@bp.route('/api/schedules')
@login_required
def api_schedules():
    schedules = Schedule.query.all()
    notes     = DateNote.query.all()
    company_colors = {1:'#ff9999',2:'#99ccff',3:'#99ff99',4:'#ffff99',5:'#cc99ff'}
    events = []
    # 通常スケジュール
    for s in schedules:
        start = s.date
        end   = s.end_date or s.date
        abbrev = s.company.company_name[:2]
        events.append({
            "id": f"sch-{s.id}",
            "title": abbrev,
            "start": start.isoformat(),
            "end": (end + timedelta(days=1)).isoformat(),
            "color": company_colors.get(s.company_id, '#cccccc'),
            "textColor": "#000",
            "allDay": True,
            "extendedProps": {
                "fullTitle": f"{s.time_slot} {s.task_name}",
                "site": s.site_name,
                "person": s.person_in_charge
            }
        })
    # 日付メモ（背景表示）
    for n in notes:
        events.append({
            "id": f"memo-{n.id}",
            "start": n.date.isoformat(),
            "allDay": True,
            "display": "background",  # 背景モード
            "color": "#ffcc00",
            "extendedProps": {
                "memo": n.client_comment or '',
                "person": n.client_person or ''
            }
        })
    return jsonify(events)

@bp.route('/schedules/<int:id>', methods=['GET', 'POST'])
@login_required
def schedule_detail(id):
    schedule = Schedule.query.get_or_404(id)
    if request.method == 'POST' and current_user.id == schedule.company_id:
        schedule.time_slot        = request.form['time_slot']
        schedule.task_name        = request.form['task_name']
        schedule.person_in_charge = request.form['person_in_charge']
        schedule.comment          = request.form['comment']
        db.session.commit()
        flash('予定を更新しました', 'success')
        return redirect(url_for('main.schedule_calendar'))
    return render_template('schedule/detail.html', schedule=schedule)

@bp.route('/schedules/add', methods=['POST'])
@login_required
def schedule_add():
    date_val     = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    end_date_str = request.form.get('end_date')
    end_date     = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    new = Schedule(
        site_name        = request.form['site_name'],
        date             = date_val,
        end_date         = end_date,
        company_id       = current_user.id,
        time_slot        = request.form['time_slot'],
        task_name        = request.form['task_name'],
        person_in_charge = request.form['person_in_charge'],
        comment          = request.form.get('comment'),
        client_person    = request.form.get('client_person'),
        client_comment   = request.form.get('client_comment'),
        created_by       = current_user.id
    )
    db.session.add(new)
    db.session.commit()
    return redirect(url_for('main.schedule_by_date', date_str=date_val.strftime('%Y-%m-%d')))

@bp.route('/schedules/delete/<int:id>', methods=['POST'])
@login_required
def schedule_delete(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.company_id == current_user.id:
        db.session.delete(schedule)
        db.session.commit()
        flash('予定を削除しました', 'success')
    else:
        flash('自社の予定のみ削除できます', 'danger')
    return redirect(url_for('main.schedule_by_date', date_str=schedule.date.strftime('%Y-%m-%d')))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()  # 実際は RegisterForm
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('…', 'danger')
            return redirect(url_for('main.register'))
        user = User(...)
        db.session.add(user)
        db.session.commit()
        flash('…', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/schedules/client/comment/<int:id>', methods=['GET','POST'])
@login_required
def edit_client_comment(id):
    # データ取得
    schedule = Schedule.query.get_or_404(id)

    # 発注元ユーザーのみ編集可
    if current_user.company_name != '菱輝金型工業':
        flash('権限がありません', 'danger')
        return redirect(url_for('main.schedule_calendar'))

    if request.method == 'POST':
        # フォームから値を取得して更新
        schedule.client_person  = request.form.get('client_person', '')
        schedule.client_comment = request.form.get('client_comment', '')
        db.session.commit()
        flash('発注元コメントを更新しました', 'success')
        return redirect(url_for('main.schedule_calendar'))

    # GET のときはフォーム画面を表示
    return render_template(
        'schedule/client_comment_form.html',  # ← テンプレート名を明示
        schedule=schedule                   # ← テンプレートで使う変数
    )

@bp.route('/schedules/client/comment/delete/<int:id>', methods=['POST'])
@login_required
def delete_client_comment(id):
    note = DateNote.query.get_or_404(id)

    # 発注元のみ削除可
    if current_user.company_name != '菱輝金型工業':
        flash('権限がありません', 'danger')
    else:
        db.session.delete(note)
        db.session.commit()
        flash('発注元コメントを削除しました', 'success')

    # 詳細ページ（同じ日付）の一覧に戻す
    return redirect(
        url_for('main.schedule_by_date',
                date_str=note.date.strftime('%Y-%m-%d'))
    )


@bp.route('/schedules/date/<date_str>', methods=['GET','POST'])
@login_required
def schedule_by_date(date_str):
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    schedules = (
        Schedule.query
        .filter(Schedule.date <= selected_date)
        .filter(or_(Schedule.end_date >= selected_date, Schedule.end_date.is_(None)))
        .all()
    )
    note = DateNote.query.filter_by(date=selected_date).first()
    if request.method == 'POST':
        if current_user.company_name != '菱輝金型工業':
            # 一括更新…
            flash('予定を更新しました', 'success')
        else:
            # メモ更新／追加…
            flash('メモを更新しました', 'success')
        db.session.commit()
        return redirect(url_for('main.schedule_by_date', date_str=date_str))
    max_end_date = max((s.end_date or s.date) for s in schedules) if schedules else selected_date
    return render_template(
        'schedule/by_date.html',
        schedules     = schedules,
        selected_date = selected_date,
        date_note     = note,
        max_end_date  = max_end_date
    )

