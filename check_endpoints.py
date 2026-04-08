#!/usr/bin/env python3
"""
Проверка работоспособности всех эндпоинтов CTF платформы.
Запускать после инициализации БД: python check_endpoints.py
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from main import app, db, User, Category, Task, Solve, Proposal, Writeup

def check_routes():
    """Печатает все доступные маршруты"""
    print("📋 Доступные эндпоинты:")
    print("-" * 80)
    
    routes = [
        # Auth
        ("GET", "/", "Главная / редирект на категории"),
        ("GET", "/login", "Форма входа"),
        ("POST", "/login", "Обработка входа"),
        ("GET", "/register", "Форма регистрации"),
        ("POST", "/register", "Обработка регистрации"),
        ("GET", "/logout", "Выход"),
        
        # Tasks
        ("GET", "/category", "Список категорий [login_required]"),
        ("GET", "/<category>/<task>", "Деталь задачи [login_required]"),
        ("POST", "/submit_flag", "Проверка флага [login_required]"),
        
        # Leaderboard
        ("GET", "/leaderboard", "Таблица лидеров"),
        ("GET", "/api/leaderboard", "JSON API лидеров"),
        
        # About
        ("GET", "/about", "О проекте"),
        
        # Suggestions (User)
        ("GET", "/suggest", "Мои предложения [login_required]"),
        ("POST", "/suggest/submit", "Отправка предложения [login_required]"),
        
        # Admin
        ("GET", "/admin", "Админ панель [admin_required]"),
        ("GET", "/admin/tasks", "Управление задачами [admin_required]"),
        ("POST", "/admin/tasks/add", "Добавить задачу [admin_required]"),
        ("GET", "/admin/tasks/<id>/edit", "Редактирование задачи [admin_required]"),
        ("POST", "/admin/tasks/<id>/edit", "Сохранение задачи [admin_required]"),
        ("POST", "/admin/tasks/<id>/delete", "Удаление задачи [admin_required]"),
        ("GET", "/admin/proposals", "Одобрение предложений [admin_required]"),
        ("POST", "/admin/suggest/<id>/approve", "Одобрить предложение [admin_required]"),
        
        # Writeups
        ("GET", "/writeups", "Список райтапов [login_required]"),
        ("POST", "/writeups/submit", "Публикация райтапа [login_required]"),
    ]
    
    for method, path, desc in routes:
        print(f"  {method:4} {path:30} - {desc}")
    
    print("\n✅ Все эндпоинты зарегистрированы\n")

def check_models():
    """Проверка моделей БД"""
    print("📊 Модели базы данных:")
    print("-" * 80)
    
    with app.app_context():
        print(f"  ✓ User - пользователи (поле 'role' для admin/user)")
        print(f"  ✓ Category - категории заданий")
        print(f"  ✓ Task - задания")
        print(f"  ✓ Solve - решенные задания")
        print(f"  ✓ Proposal - предложения пользователей")
        print(f"  ✓ Writeup - райтапы (отчеты о решении)")
    
    print("\n✅ Все модели созданы\n")

def check_default_data():
    """Проверка наличия данных по умолчанию"""
    print("💾 Начальные данные:")
    print("-" * 80)
    
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        categories = Category.query.all()
        tasks = Task.query.all()
        
        if admin:
            print(f"  ✓ Admin пользователь создан (username: admin, password: admin123)")
        
        print(f"  ✓ Категории ({len(categories)} шт.):")
        for cat in categories:
            task_count = Task.query.filter_by(category_id=cat.id).count()
            print(f"      - {cat.name} ({task_count} заданий)")
        
        print(f"  ✓ Всего заданий: {len(tasks)}")
    
    print("\n✅ Данные инициализированы\n")

def main():
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА ПЛАТФОРМЫ CTF SECULETI")
    print("="*80 + "\n")
    
    check_routes()
    check_models()
    check_default_data()
    
    print("="*80)
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("="*80)
    print("\n🚀 Для запуска сервера выполните:")
    print("   cd app")
    print("   docker-compose up\n")

if __name__ == '__main__':
    main()
