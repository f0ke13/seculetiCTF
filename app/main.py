from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from config import DB_CONFIG
from functools import wraps
from datetime import datetime, timedelta, timezone
import bcrypt
import os

MSK = timezone(timedelta(hours=3))

POSTGRES_USER = DB_CONFIG['user']
POSTGRES_PASSWORD = DB_CONFIG['password']
POSTGRES_DB = DB_CONFIG['database']
POSTGRES_HOST = DB_CONFIG['host']

# Абсолютный путь к шаблонам - Docker монтирует front_end-demo в /app/front_end-demo
app = Flask(__name__, template_folder='/app/front_end-demo')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}'
db = SQLAlchemy()
db.init_app(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, admin


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    flag_hash = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=100)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)


class Solve(db.Model):
    __tablename__ = "solves"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)
    points_awarded = db.Column(db.Integer, default=0)
    is_forfeit = db.Column(db.Boolean, default=False)


class Proposal(db.Model):
    __tablename__ = "proposals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    difficulty = db.Column(db.String(50), default='medium')
    points = db.Column(db.Integer, default=100)
    flag = db.Column(db.String(255), nullable=False)
    hints = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Writeup(db.Model):
    __tablename__ = "writeups"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('category'))
    return render_template('main.html')


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password'].encode('utf-8')
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password, user.password.encode()):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('category'))
    flash('Invalid credentials', 'error')
    return render_template('login.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form['username']
    password = request.form['password'].encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, password=hashed)
    try:
        db.session.add(user)
        db.session.commit()
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    except IntegrityError:
        db.session.rollback()
        flash('Username already exists', 'error')
    return render_template('register.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Доступ запрещен', 'error')
            return redirect(url_for('category'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/category', methods=['GET'])
@login_required
def category():
    categories = Category.query.all()
    tasks = Task.query.all()
    solved = Solve.query.filter_by(user_id=session['user_id'], is_forfeit=False).all()
    solved_task_ids = [s.task_id for s in solved]
    return render_template('category.html', categories=categories, tasks=tasks, solved_tasks=solved_task_ids)


# === НОВАЯ СДАЧА ФЛАГА (JSON + работает на любой странице) ===
@app.route("/submit_flag", methods=["POST"])
@login_required
def submit_flag():
    submitted_flag = request.form.get('flag', '').encode('utf-8')

    for task in Task.query.all():
        if bcrypt.checkpw(submitted_flag, task.flag_hash.encode()):
            already = Solve.query.filter_by(
                user_id=session['user_id'],
                task_id=task.id
            ).first()

            if not already:
                solve = Solve(
                    user_id=session['user_id'],
                    task_id=task.id,
                    points_awarded=task.points,
                    is_forfeit=False,
                )
                db.session.add(solve)
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": f"Correct flag! +{task.points} баллов.",
                    "points": task.points,
                    "task": task.title,
                })
            if already.is_forfeit:
                already.points_awarded = task.points
                already.is_forfeit = False
                already.solved_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": f"Correct flag! +{task.points} баллов.",
                    "points": task.points,
                    "task": task.title,
                })
            return jsonify({"success": False, "message": "Уже решено"})

    return jsonify({"success": False, "message": "Неверный флаг"})


@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')


@app.route('/api/leaderboard')
def api_leaderboard():
    """JSON-эндпоинт: рейтинг игроков по сумме баллов за решённые задания."""
    total_tasks = Task.query.count()

    rows = (
        db.session.query(
            User.username,
            db.func.coalesce(db.func.sum(Solve.points_awarded), 0).label('score'),
            db.func.count(Solve.id).label('solved'),
            db.func.max(Solve.solved_at).label('last_solve'),
        )
        .join(Solve, Solve.user_id == User.id)
        .filter(Solve.is_forfeit == False)
        .group_by(User.id, User.username)
        .order_by(db.desc('score'), db.asc('last_solve'))
        .all()
    )

    players = []
    for r in rows:
        last_msk = '-'
        if r.last_solve:
            # stored as naive UTC → attach UTC, convert to MSK
            utc_dt = r.last_solve.replace(tzinfo=timezone.utc)
            last_msk = utc_dt.astimezone(MSK).strftime('%H:%M')
        players.append({
            'username': r.username,
            'score': int(r.score),
            'solved': int(r.solved),
            'last_solve': last_msk,
        })

    now_msk = datetime.now(MSK)
    return jsonify({
        'players': players,
        'total_tasks': total_tasks,
        'server_time': now_msk.strftime('%d %b %Y %H:%M:%S MSK'),
    })


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/osint')
@login_required
def osint():
    # Получаем задание "Анонимный спортсмен"
    task = Task.query.filter_by(title="Анонимный спортсмен").first()
    solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task.id, is_forfeit=False).first() is not None if task else False
    return render_template('osint.html', task=task, solved=solved)


@app.route('/beginner')
@login_required
def beginner():
    # Получаем задания Beginner по названиям
    task1 = Task.query.filter_by(title="Без комментариев").first()
    task2 = Task.query.filter_by(title="Little Osinter").first()
    task3 = Task.query.filter_by(title="Крипто-ключ").first()
    
    # Проверяем решены ли задания
    task1_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task1.id, is_forfeit=False).first() is not None if task1 else False
    task2_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task2.id, is_forfeit=False).first() is not None if task2 else False
    task3_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task3.id, is_forfeit=False).first() is not None if task3 else False
    
    return render_template('begginer.html', 
                           task1_solved=task1_solved,
                           task2_solved=task2_solved,
                           task3_solved=task3_solved)


# ===== ЭНДПОИНТЫ ПРЕДЛОЖЕНИЙ =====
@app.route('/suggest', methods=['GET'])
@login_required
def suggest():
    proposals = Proposal.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.all()
    return render_template('proposals.html', proposals=proposals, categories=categories)


@app.route('/suggest/submit', methods=['POST'])
@login_required
def suggest_submit():
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    points = request.form.get('points', 100)
    flag = request.form.get('flag')
    hints = request.form.get('hints', '')
    difficulty = request.form.get('difficulty', 'medium')
    
    if not all([title, category_id, description, flag]):
        flash('Заполните все обязательные поля', 'error')
        return redirect(url_for('suggest'))
        
    if Proposal.query.filter_by(title=title).first() or Task.query.filter_by(title=title).first():
        flash('Задача с таким названием уже существует', 'error')
        return redirect(url_for('suggest'))
        
    p = Proposal(
        user_id=session['user_id'],
        title=title,
        description=description,
        category_id=int(category_id),
        difficulty=difficulty,
        points=int(points) if str(points).isdigit() else 100,
        flag=flag,
        hints=hints
    )
    db.session.add(p)
    db.session.commit()
    flash('Отправлено на проверку', 'success')
    return redirect(url_for('suggest'))


# ===== ЭНДПОИНТЫ АДМИН ПАНЕЛИ =====
@app.route('/admin')
@admin_required
def admin_dashboard():
    user_count = User.query.count()
    task_count = Task.query.count()
    pending_proposals = Proposal.query.filter_by(status='pending').count()
    return render_template('admin.html', user_count=user_count, task_count=task_count, pending_proposals=pending_proposals)


@app.route('/admin/tasks')
@admin_required
def admin_tasks():
    tasks = Task.query.all()
    categories = Category.query.all()
    return render_template('admin_tasks.html', tasks=tasks, categories=categories)


@app.route('/admin/tasks/add', methods=['POST'])
@admin_required
def admin_tasks_add():
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    description = request.form.get('description')
    points = request.form.get('points', 100)
    flag = request.form.get('flag')
    
    if not all([title, category_id, description, flag]):
        flash('Заполните все обязательные поля', 'error')
        return redirect(url_for('admin_tasks'))
        
    if Task.query.filter_by(title=title).first():
        flash('Задача с таким названием уже существует', 'error')
        return redirect(url_for('admin_tasks'))
        
    flag_hash = bcrypt.hashpw(flag.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    t = Task(
        title=title,
        description=description,
        flag_hash=flag_hash,
        points=int(points) if str(points).isdigit() else 100,
        category_id=int(category_id)
    )
    db.session.add(t)
    db.session.commit()
    flash('Задача добавлена', 'success')
    return redirect(url_for('admin_tasks'))


@app.route('/admin/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_tasks_edit(task_id):
    task = Task.query.get_or_404(task_id)
    categories = Category.query.all()
    if request.method == 'GET':
        return render_template('edit_task.html', task=task, categories=categories)
        
    task.title = request.form.get('title', task.title)
    task.category_id = int(request.form.get('category_id', task.category_id))
    task.description = request.form.get('description', task.description)
    task.points = int(request.form.get('points', task.points))
    
    flag = request.form.get('flag')
    if flag:
        task.flag_hash = bcrypt.hashpw(flag.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
    db.session.commit()
    flash('Задача обновлена', 'success')
    return redirect(url_for('admin_tasks'))


@app.route('/admin/tasks/<int:task_id>/delete', methods=['POST'])
@admin_required
def admin_tasks_delete(task_id):
    if request.form.get('confirm') == 'yes':
        task = Task.query.get_or_404(task_id)
        Solve.query.filter_by(task_id=task.id).delete()
        Writeup.query.filter_by(task_id=task.id).delete()
        db.session.delete(task)
        db.session.commit()
        flash('Задача удалена', 'success')
    return redirect(url_for('admin_tasks'))


@app.route('/admin/proposals', methods=['GET'])
@admin_required
def admin_proposals():
    proposals = Proposal.query.filter_by(status='pending').all()
    categories = Category.query.all()
    return render_template('admin_proposals.html', proposals=proposals, categories=categories)


@app.route('/admin/suggest/<int:prop_id>/approve', methods=['POST'])
@admin_required
def admin_suggest_approve(prop_id):
    proposal = Proposal.query.get_or_404(prop_id)
    
    proposal.title = request.form.get('title', proposal.title)
    proposal.description = request.form.get('description', proposal.description)
    proposal.points = int(request.form.get('points', proposal.points))
    
    flag = request.form.get('flag', proposal.flag)
    flag_hash = bcrypt.hashpw(flag.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    t = Task(
        title=proposal.title,
        description=proposal.description,
        flag_hash=flag_hash,
        points=proposal.points,
        category_id=proposal.category_id
    )
    db.session.add(t)
    proposal.status = 'approved'
    db.session.commit()
    flash('Предложение одобрено и добавлено', 'success')
    return redirect(url_for('admin_proposals'))


@app.route('/admin/suggest/<int:prop_id>/reject', methods=['POST'])
@admin_required
def admin_suggest_reject(prop_id):
    proposal = Proposal.query.get_or_404(prop_id)
    proposal.status = 'rejected'
    db.session.commit()
    flash('Предложение отклонено', 'success')
    return redirect(url_for('admin_proposals'))


# ===== ЭНДПОИНТЫ РАЙТАПОВ =====
@app.route('/writeups', methods=['GET'])
@login_required
def writeups():
    task_id = request.args.get('task_id', type=int)

    allowed = Solve.query.filter_by(user_id=session['user_id']).all()
    allowed_task_ids = {s.task_id for s in allowed}

    if task_id and task_id not in allowed_task_ids:
        flash('Для доступа к райтапам решите задачу или выберите просмотр с 0 баллов.', 'error')
        return redirect(url_for('category'))

    query = Writeup.query
    if task_id:
        query = query.filter_by(task_id=task_id)
    else:
        query = query.filter(Writeup.task_id.in_(allowed_task_ids))

    ws = query.all()
    tasks = Task.query.all()

    writeups_formatted = []
    for w in ws:
        user = User.query.get(w.user_id)
        task = Task.query.get(w.task_id)
        writeups_formatted.append((w, user.username if user else 'Unknown', task.title if task else 'Unknown'))

    return render_template('writeups.html', writeups=writeups_formatted, tasks=tasks, current_task_id=task_id)


@app.route('/writeups/submit', methods=['POST'])
@login_required
def writeups_submit():
    task_id = request.form.get('task_id')
    content = request.form.get('content')
    if not task_id or not content:
        flash('Заполните все поля', 'error')
        return redirect(url_for('writeups'))
        
    solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task_id, is_forfeit=False).first()
    if not solved:
        flash('Нельзя опубликовать райтап для нерешённого задания', 'error')
        return redirect(url_for('writeups'))
        
    existing = Writeup.query.filter_by(user_id=session['user_id'], task_id=task_id).first()
    if existing:
        flash('Вы уже добавили райтап для этого задания', 'error')
        return redirect(url_for('writeups'))
        
    w = Writeup(user_id=session['user_id'], task_id=task_id, content=content)
    db.session.add(w)
    db.session.commit()
    flash('Райтап добавлен', 'success')
    return redirect(url_for('writeups'))


@app.route('/tasks/<int:task_id>/forfeit', methods=['POST'])
@login_required
def forfeit_task(task_id):
    task = Task.query.get_or_404(task_id)
    existing = Solve.query.filter_by(user_id=session['user_id'], task_id=task_id).first()

    if existing:
        if existing.is_forfeit:
            flash('Вы уже выбрали просмотр райтапов с 0 баллов.', 'error')
        else:
            flash('Задача уже решена. Райтапы доступны.', 'success')
        return redirect(request.referrer or url_for('category'))

    solve = Solve(
        user_id=session['user_id'],
        task_id=task_id,
        points_awarded=0,
        is_forfeit=True,
    )
    db.session.add(solve)
    db.session.commit()
    flash('Задача отмечена как нерешённая. Райтапы доступны (0 баллов).', 'success')
    return redirect(url_for('writeups', task_id=task_id))


# ===== ЭНДПОИНТ ДЕТАЛЬ ЗАДАЧИ =====
@app.route('/<category_name>/<task_name>')
@login_required
def task_detail(category_name, task_name):
    # Поиск категории (case-insensitive)
    categories = Category.query.all()
    category = None
    for cat in categories:
        if cat.name.lower() == category_name.lower():
            category = cat
            break
    
    if not category:
        flash('Категория не найдена', 'error')
        return redirect(url_for('category'))
    
    # Поиск задачи (может быть underscore в URL вместо пробела)
    tasks = Task.query.filter_by(category_id=category.id).all()
    task = None
    for t in tasks:
        if t.title.lower() == task_name.lower().replace('_', ' '):
            task = t
            break
    
    if not task:
        flash('Задание не найдено', 'error')
        return redirect(url_for('category'))
        
    solve_row = Solve.query.filter_by(user_id=session['user_id'], task_id=task.id).first()
    solved = solve_row is not None and not solve_row.is_forfeit
    forfeit = solve_row is not None and solve_row.is_forfeit
    return render_template('task.html', task=task, category=category, solved=solved, forfeit=forfeit)


def _ensure_task(title, description, flag_bytes, points, category_id):
    """Создаёт задание если нет, иначе — обновляет points."""
    task = Task.query.filter_by(title=title).first()
    if task:
        if task.points != points:
            task.points = points
            db.session.commit()
        return task
    hashed = bcrypt.hashpw(flag_bytes, bcrypt.gensalt()).decode('utf-8')
    task = Task(
        title=title,
        description=description,
        flag_hash=hashed,
        points=points,
        category_id=category_id,
    )
    db.session.add(task)
    db.session.commit()
    return task


def seed():
    # Создаём админа если его нет
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        admin = User(username='admin', password=hashed, role='admin')
        db.session.add(admin)
        db.session.commit()
    
    # OSINT категория
    osint_cat = Category.query.filter_by(name="OSINT").first()
    if not osint_cat:
        osint_cat = Category(name="OSINT")
        db.session.add(osint_cat)
        db.session.commit()

    _ensure_task(
        title="Анонимный спортсмен",
        description="Привет, я слышал, что ты можешь вычислить человека по IP...",
        flag_bytes=b"seculeti{Pr0f1t}",
        points=1000,
        category_id=osint_cat.id,
    )

    # Beginner категория
    beginner_cat = Category.query.filter_by(name="Beginner").first()
    if not beginner_cat:
        beginner_cat = Category(name="Beginner")
        db.session.add(beginner_cat)
        db.session.commit()

    _ensure_task(
        title="Без комментариев",
        description="Все с чего-то начинают, даже если у тебя нет инструментов для этого.",
        flag_bytes=b"seculeti{Plz_D0nt_C0mm3nt_th1$}",
        points=15,
        category_id=beginner_cat.id,
    )

    _ensure_task(
        title="Little Osinter",
        description="Команда seculeti уже десятый раз меняет название своей группы...",
        flag_bytes=b"seculeti{3350971088}",
        points=25,
        category_id=beginner_cat.id,
    )

    _ensure_task(
        title="Крипто-ключ",
        description="Сколько раз говорить ему не оставлять пароли на столе..",
        flag_bytes=b"seculeti{Th4t$T0oCl1ch3N0tEv3rCrypt0}",
        points=15,
        category_id=beginner_cat.id,
    )


def migrate_db():
    """Добавляет недостающие колонки в существующие таблицы"""
    from sqlalchemy import text

    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='tasks' AND column_name='points'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN points INTEGER DEFAULT 100"))
            conn.commit()

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='solves' AND column_name='points_awarded'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE solves ADD COLUMN points_awarded INTEGER DEFAULT 0"))
            conn.commit()

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='solves' AND column_name='is_forfeit'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE solves ADD COLUMN is_forfeit BOOLEAN DEFAULT FALSE"))
            conn.commit()

        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """))
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            conn.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_db()
        seed()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)