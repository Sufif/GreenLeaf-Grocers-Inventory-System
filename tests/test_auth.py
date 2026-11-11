def test_login_page(client):
    r = client.get('/login')
    assert r.status_code == 200
    assert b'GreenLeaf' in r.data


def test_login_success(client):
    r = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert r.status_code == 200
    assert b'Dashboard' in r.data or b'dashboard' in r.data.lower()


def test_login_failure(client):
    r = client.post('/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
    assert b'Invalid' in r.data or b'invalid' in r.data.lower()


def test_logout(admin_client):
    r = admin_client.get('/logout', follow_redirects=True)
    assert r.status_code == 200
    assert b'Login' in r.data or b'login' in r.data.lower()
