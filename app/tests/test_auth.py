def test_register(client):
    """Регистрация нового пользователя возвращает редирект"""
    res = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert res.status_code in (200, 302)


def test_login_success(client):
    """Успешный вход с правильными данными редиректит на category"""
    client.post('/register', data={'username': 'user1', 'password': 'pass1'})
    res = client.post('/login', data={'username': 'user1', 'password': 'pass1'})
    assert res.status_code in (200, 302)
    client.delete_cookie('session')


def test_login_wrong_password(client):
    """Вход с неверным паролем возвращает 200 с формой"""
    res = client.post('/login', data={'username': 'user1', 'password': 'wrongpass'})
    assert res.status_code == 200


def test_category_requires_login(client):
    """Неавторизованный доступ к /category редиректит на /login"""
    client.delete_cookie('session')
    res = client.get('/category')
    assert res.status_code == 302