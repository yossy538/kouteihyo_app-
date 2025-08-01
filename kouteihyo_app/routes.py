# routes.py


from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify, session, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, extract
import jpholiday
from collections import defaultdict
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from .models import db, User, Schedule, DateNote, Company
from .forms import LoginForm, AdminUserCreateForm, DeleteNoteForm
from dateutil.parser import parse as parse_date
import re
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def is_strong_password(pw):
    return (
        len(pw) >= 8 and
        bool(re.search(r'[A-Z]', pw)) and
        bool(re.search(r'[a-z]', pw)) and
        bool(re.search(r'[0-9]', pw)) and
        bool(re.search(r'[^A-Za-z0-9]', pw))
    )



bp = Blueprint('main', __name__)

@bp.before_request
def enforce_password_change():
    # 必ずDB最新を参照
    if current_user.is_authenticated:
        user_fresh = User.query.filter_by(id=current_user.id).first()
        if user_fresh and getattr(user_fresh, "must_change_password", False):
            allowed_endpoints = ['main.force_password_change', 'main.logout', 'static']
            if request.endpoint not in allowed_endpoints:
                # ★flashは絶対にしない（リダイレクトのみ！）
                return redirect(url_for('main.force_password_change'))



# ログイン
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    from flask_login import current_user  # 必ずここでimport
    logger.info("【login関数】METHOD: %s", request.method)
    logger.info("【login関数】POST DATA: %s", request.form)
    logger.info("【login関数】form.errors(before validate): %s", form.errors)
    logger.info("【login関数】form.validate_on_submit(): %s", form.validate_on_submit())

    user = None  # これ重要！

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            logger.info("【login_user called】user.id = %s", user.id)
            logger.info("【is_authenticated after login_user】%s", current_user.is_authenticated)
            from flask import session
            logger.info("【session after login_user】%s", dict(session))
            session.permanent = True
            if user.must_change_password:
                return redirect(url_for('main.force_password_change'))
            return redirect(url_for('main.schedule_calendar'))
        else:
            flash('ユーザー名またはパスワードが違います', 'danger')
            logger.info("【login関数】ログイン失敗: user=%s", user)

    logger.info("【login関数】LOGIN ERRORS: %s", form.errors)
    return render_template('login.html', form=form)





# ログアウト
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# 一覧表示
@bp.route('/schedules')
@login_required
def schedule_list():
    if current_user.role == 'admin':
        schedules = Schedule.query.order_by(Schedule.date.asc()).all()
    else:
        schedules = (
            Schedule.query
            .filter_by(company_id=current_user.company_id)
            .order_by(Schedule.date.asc())
            .all()
        )
    schedules_by_date = defaultdict(list)
    for s in schedules:
        schedules_by_date[s.date.strftime('%Y-%m-%d')].append(s)
    return render_template('schedule/list.html', schedules_by_date=schedules_by_date)

# カレンダー表示
@bp.route('/schedules/calendar')
@login_required
def schedule_calendar():
    today = datetime.today()
    year, month = today.year, today.month
    # 祝日
    holiday_list = [d.strftime('%Y-%m-%d') for d, _ in jpholiday.month_holidays(year, month)]
    # クライアント会社のメモ取得
    client_company = Company.query.filter_by(name='菱輝金型工業').first()
    client_ids = [u.id for u in client_company.users] if client_company else []
    notes = (
        DateNote.query
        .filter(extract('year', DateNote.date)==year)
        .filter(extract('month', DateNote.date)==month)
        .filter(DateNote.created_by.in_(client_ids))
        .all()
    )
    note_list = [n.date.strftime('%Y-%m-%d') for n in notes]
    return render_template(
        'schedule/calendar.html',
        holiday_list=holiday_list,
        note_list=note_list
    )

# API: スケジュール一覧
@bp.route('/api/schedules')
@login_required
def api_schedules():
    schedules = Schedule.query.all()
    notes = DateNote.query.all()
    colors = {1:'#99ccff',2:'#99ff99',3:'#ff9999',4:'#cc99ff',5:'#ffff99'}
    events = []
    for s in schedules:
        start = s.date
        end = s.end_date or s.date
        abbrev = s.company.name[:2]
        events.append({
            'id': f'sch-{s.id}',
            'title': abbrev,
            'start': start.isoformat(),
            'end': (end + timedelta(days=1)).isoformat(),
            'color': colors.get(s.company_id, '#cccccc'),
            'textColor': 'black',
            'allDay': True,
            'extendedProps': {
                'fullTitle': f"{s.time_slot} {s.task_name}",
                'site': s.site_name,
                'person': s.person_in_charge
            }
        })
    # メモ（背景表示）
    for n in notes:
        events.append({
            'id': f'memo-{n.id}',
            'start': n.date.isoformat(),
            'display': 'background',
            'color': '#FF90BB',
            'extendedProps': {
                'memo': n.client_comment or '',
                'person': n.client_person or ''
            }
        })
    return jsonify(events)

# 詳細表示・更新
@bp.route('/schedules/<int:id>', methods=['GET','POST'])
@login_required
def schedule_detail(id):
    schedule = Schedule.query.get_or_404(id)
    if request.method == 'POST' and current_user.company_id == schedule.company_id:
        schedule.time_slot = request.form['time_slot']
        schedule.task_name = request.form['task_name']
        schedule.person_in_charge = request.form['person_in_charge']
        schedule.comment = request.form['comment']
        db.session.commit()
        flash('予定を更新しました', 'success')
        return redirect(url_for('main.schedule_calendar'))
    return render_template('schedule/detail.html', schedule=schedule)

# 追加
@bp.route('/schedules/add', methods=['POST'])
@login_required
def schedule_add():
    date_val = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    end_date_str = request.form.get('end_date')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    new = Schedule(
        site_name=request.form['site_name'],
        date=date_val,
        end_date=end_date,
        company_id=current_user.company_id,
        time_slot=request.form['time_slot'],
        task_name=request.form['task_name'],
        person_in_charge=request.form['person_in_charge'],
        comment=request.form.get('comment'),
        client_person=request.form.get('client_person'),
        client_comment=request.form.get('client_comment'),
        created_by=current_user.id
    )
    db.session.add(new)
    db.session.commit()
    return redirect(url_for('main.schedule_by_date', date_str=date_val.strftime('%Y-%m-%d')))


@bp.route('/schedules/delete/<int:id>', methods=['POST'])
@login_required
def schedule_delete(id):
    schedule = Schedule.query.get_or_404(id)
    if schedule.company_id == current_user.company_id:
        db.session.delete(schedule)
        db.session.commit()
        flash('予定を削除しました', 'success')
    else:
        flash('自社の予定のみ削除できます', 'danger')
    return redirect(url_for('main.schedule_by_date', date_str=schedule.date.strftime('%Y-%m-%d')))



@bp.route('/schedules/client/comment/<int:id>', methods=['GET','POST'])
@login_required
def edit_client_comment(id):
    # データ取得
    schedule = Schedule.query.get_or_404(id)

    # 発注元ユーザーのみ編集可
    if current_user.company.name != '菱輝金型工業':
        flash('権限がありません', 'danger')
        return redirect(url_for('main.schedule_calendar'))

    if request.method == 'POST':
        # フォームから値を取得して更新
        schedule.client_person  = request.form.get('client_person', '')
        schedule.client_comment = request.form.get('client_comment', '')
        db.session.commit()
        flash('発注元コメントを更新しました', 'success')
         # 更新後は「日付詳細」ページに戻す
        date_str = schedule.date.strftime('%Y-%m-%d')
        return redirect(url_for('main.schedule_by_date', date_str=date_str))

    # GET のときはフォーム画面を表示
    return render_template(
        'schedule/client_comment_form.html',  # ← テンプレート名を明示
        schedule=schedule                   # ← テンプレートで使う変数
    )

@bp.route('/schedules/client/comment/delete/<int:id>', methods=['POST'])
@login_required
def delete_client_comment(id):
    note = DateNote.query.get_or_404(id)
    if current_user.company.name != '菱輝金型工業':
        flash('権限がありません', 'danger')
    else:
        db.session.delete(note)
        db.session.commit()
        flash('スケジュールメモを削除しました', 'success')
    return redirect(url_for('main.schedule_by_date', date_str=note.date.strftime('%Y-%m-%d')))





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
        # 発注元のみメモの更新／追加を許可
        if current_user.company.name == '菱輝金型工業':   # ←ここ修正
            person  = request.form.get('client_person', '').strip()
            comment = request.form.get('client_comment', '').strip()
            if note:
                note.client_person  = person
                note.client_comment = comment
            else:
                note = DateNote(
                    date           = selected_date,
                    client_person  = person,
                    client_comment = comment,
                    created_by     = current_user.id
                )
                db.session.add(note)
            db.session.commit()
            flash('メモを更新しました', 'success')
        else:
            # 協力会社側の一括スケジュール更新ロジック
            for s in schedules:
                if s.company_id == current_user.company_id:  # ←ここ修正
                    s.person_in_charge = request.form.get(f'person_in_charge_{s.id}', s.person_in_charge)
                    s.time_slot = request.form.get(f'time_slot_{s.id}', s.time_slot)
                    s.task_name = request.form.get(f'task_name_{s.id}', s.task_name)
                    s.comment = request.form.get(f'comment_{s.id}', s.comment)
            db.session.commit()
            flash('予定を更新しました', 'success')

        return redirect(url_for('main.schedule_by_date', date_str=date_str))

    max_end_date = (
        max((s.end_date or s.date) for s in schedules)
        if schedules else selected_date
    )
    delete_form = DeleteNoteForm()

    return render_template(
        'schedule/by_date.html',
        schedules     = schedules,
        selected_date = selected_date,
        date_note     = note,
        max_end_date  = max_end_date,
        delete_form   = delete_form
    )

@bp.route('/api/note_list')
@login_required
def api_note_list():
    start = request.args.get('start')
    end = request.args.get('end')
    try:
        start_date = parse_date(start).date() if start else None
        end_date = parse_date(end).date() if end else None
    except Exception as e:
        logger.error("date parse error: %s", e)
        return jsonify({"error": "Invalid date format"}), 400


    # 発注元会社IDを特定（例：菱輝金型工業）
    client_company = Company.query.filter_by(name='菱輝金型工業').first()
    client_ids = [u.id for u in client_company.users] if client_company else []

    # 日付範囲のメモを取得（created_byが発注元のみ）
    q = DateNote.query
    if start_date: q = q.filter(DateNote.date >= start_date)
    if end_date: q = q.filter(DateNote.date <= end_date)
    q = q.filter(DateNote.created_by.in_(client_ids))

    notes = q.all()
    note_list = [
        {
            "date": n.date.isoformat(),
            "client_person": n.client_person,
            "client_comment": n.client_comment,
        } for n in notes
    ]
    return jsonify(note_list=note_list)

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import current_user, login_required

@bp.route('/password_change', methods=['GET', 'POST'])
@login_required
def password_change():
    if request.method == 'POST':
        old = request.form.get('old_password')
        new = request.form.get('new_password')
        new2 = request.form.get('new_password2')
        if not check_password_hash(current_user.password_hash, old):
            flash('現在のパスワードが違います', 'danger')
            return redirect(url_for('main.password_change'))
        elif new != new2:
            flash('新しいパスワードが一致しません', 'danger')
            return redirect(url_for('main.password_change'))
        elif len(new) < 8:
            flash('パスワードは8文字以上にしてください', 'danger')
            return redirect(url_for('main.password_change'))
        else:
            current_user.password_hash = generate_password_hash(new)
            db.session.commit()
            flash('パスワードを変更しました', 'success')
            return redirect(url_for('main.schedule_calendar'))  # ←カレンダーなどTOPへ
    return render_template('auth/password_change.html')



@bp.route("/admin/list_users")
@login_required
def admin_list_users():
    if current_user.role != 'admin':
        abort(403)
    users = User.query.all()  # ← 必ずリストを作る！
    return render_template("admin/user_list.html", users=users)


@bp.route("/admin/create_user", methods=["GET", "POST"])
@login_required
def admin_create_user():
    if current_user.role != 'admin':
        abort(403)
    form = AdminUserCreateForm()
    form.company_id.choices = [(c.id, c.name) for c in Company.query.order_by(Company.name).all()]

    if form.validate_on_submit():
        # 既に同じusernameやemailがあるかチェック
        if User.query.filter_by(username=form.username.data).first():
            flash('このユーザー名は既に使われています', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('このメールアドレスは既に使われています', 'danger')
        else:
            user = User(
                company_id=form.company_id.data,
                display_name=form.display_name.data,
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                role=form.role.data,
                must_change_password=True   # ←★これを**必ず追加**！
            )
            db.session.add(user)
            db.session.commit()
            flash('ユーザーを作成しました', 'success')
            return redirect(url_for('main.admin_list_users'))

    return render_template("admin/user_new.html", form=form)


@bp.route('/force_password_change', methods=['GET', 'POST'])
@login_required
def force_password_change():
    if not current_user.must_change_password:
        return redirect(url_for('main.schedule_calendar'))
    if request.method == 'POST':
        old_pw = request.form['old_password']
        new_pw = request.form['new_password']
        new_pw2 = request.form['new_password2']
        if not check_password_hash(current_user.password_hash, old_pw):
            flash('現在のパスワードが違います', 'danger')
        elif new_pw != new_pw2:
            flash('新しいパスワードが一致しません', 'danger')
        elif len(new_pw) < 8:
            flash('パスワードは8文字以上で設定してください', 'danger')
        elif not is_strong_password(new_pw):
            flash('パスワードは英大文字・小文字・数字・記号を全て含めてください', 'danger')
        else:
            current_user.password_hash = generate_password_hash(new_pw)
            current_user.must_change_password = False
            db.session.commit()
            flash('パスワードが変更されました', 'success')
            return redirect(url_for('main.schedule_calendar'))
    return render_template('auth/password_change.html')


@bp.route('/')
def index():
    # ログイン済みならカレンダーへ
    if current_user.is_authenticated:
        return redirect(url_for('main.schedule_calendar'))
    # 未ログインならログイン画面へ
    return redirect(url_for('main.login'))

# kouteihyo_app/routes.py の一番下
__all__ = ["is_strong_password"]
