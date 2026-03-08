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

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}'
db = SQLAlchemy()
db.init_app(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


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
        flash('Logged in successfully', 'success')
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


@app.route('/category', methods=['GET'])
@login_required
def category():
    categories = Category.query.all()
    tasks = Task.query.all()
    solved = Solve.query.filter_by(user_id=session['user_id']).all()
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
                solve = Solve(user_id=session['user_id'], task_id=task.id)
                db.session.add(solve)
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": f"Correct flag! +{task.points} баллов.",
                    "points": task.points,
                    "task": task.title,
                })
            else:
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
            db.func.coalesce(db.func.sum(Task.points), 0).label('score'),
            db.func.count(Solve.id).label('solved'),
            db.func.max(Solve.solved_at).label('last_solve'),
        )
        .join(Solve, Solve.user_id == User.id)
        .join(Task, Task.id == Solve.task_id)
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
    solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task.id).first() is not None if task else False
    return render_template('osint.html', task=task, solved=solved)


@app.route('/beginner')
@login_required
def beginner():
    # Получаем задания Beginner по названиям
    task1 = Task.query.filter_by(title="Без комментариев").first()
    task2 = Task.query.filter_by(title="Little Osinter").first()
    task3 = Task.query.filter_by(title="Крипто-ключ").first()
    
    # Проверяем решены ли задания
    task1_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task1.id).first() is not None if task1 else False
    task2_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task2.id).first() is not None if task2 else False
    task3_solved = Solve.query.filter_by(user_id=session['user_id'], task_id=task3.id).first() is not None if task3 else False
    
    return render_template('begginer.html', 
                           task1_solved=task1_solved,
                           task2_solved=task2_solved,
                           task3_solved=task3_solved)


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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_db()
        seed()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)