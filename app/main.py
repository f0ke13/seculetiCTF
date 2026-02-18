from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from config import DB_CONFIG
from functools import wraps
from datetime import datetime
import bcrypt
import os

POSTGRES_USER = DB_CONFIG['user']
POSTGRES_PASSWORD = DB_CONFIG['password']
POSTGRES_DB = DB_CONFIG['database']
POSTGRES_HOST = DB_CONFIG['host']

app = Flask(__name__, template_folder='front_end-demo')
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
    return redirect(url_for('login'))


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
                return jsonify({"success": True, "message": "Correct flag! Задание решено."})
            else:
                return jsonify({"success": False, "message": "Уже решено"})

    return jsonify({"success": False, "message": "Неверный флаг"})


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


def seed():
    # OSINT категория + задание "Анонимный спортсмен"
    if not Category.query.filter_by(name="OSINT").first():
        osint_cat = Category(name="OSINT")
        db.session.add(osint_cat)
        db.session.commit()

        flag_bytes = b"seculeti{Pr0f1t}"
        hashed = bcrypt.hashpw(flag_bytes, bcrypt.gensalt()).decode('utf-8')

        task = Task(
            title="Анонимный спортсмен",
            description="Привет, я слышал, что ты можешь вычислить человека по IP...",
            flag_hash=hashed,
            category_id=osint_cat.id
        )
        db.session.add(task)
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)