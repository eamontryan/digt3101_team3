"""
TC-006: User Can Successfully Login
FR23: Support user authentication.

Preconditions: User is logged out.
Steps: Enter username/password. If correct → home page. If incorrect → error.
Expected: Successful login redirects to home page; bad creds show error.
"""
from models import db
from models.user import User
from app import bcrypt


def test_successful_login(client, app, seed_users):
    """TC-006a: Correct credentials redirect to the dashboard."""
    response = client.post('/login', data={
        'username': 'tenant_test',
        'password': 'password123',
    }, follow_redirects=True)

    assert response.status_code == 200
    html = response.data.decode()
    # Should land on the dashboard (not the login page)
    assert 'login' not in html.lower().split('logout')[0] if 'logout' in html.lower() else True
    # The presence of "dashboard" or the user's name is a good indicator
    assert 'dashboard' in html.lower() or 'test tenant' in html.lower()


def test_incorrect_password(client, app, seed_users):
    """TC-006b: Wrong password shows an error flash message."""
    response = client.post('/login', data={
        'username': 'tenant_test',
        'password': 'wrongpassword',
    }, follow_redirects=True)

    assert response.status_code == 200
    html = response.data.decode()
    assert 'invalid' in html.lower()


def test_inactive_user_blocked(client, app, seed_users):
    """TC-006c: Inactive accounts cannot log in."""
    with app.app_context():
        inactive = User(
            username='inactive_user',
            password=bcrypt.generate_password_hash('password123').decode('utf-8'),
            name='Inactive Person', email='inactive@test.com',
            role='Tenant', status='Inactive'
        )
        db.session.add(inactive)
        db.session.commit()

    response = client.post('/login', data={
        'username': 'inactive_user',
        'password': 'password123',
    }, follow_redirects=True)

    html = response.data.decode()
    assert 'not active' in html.lower() or 'contact' in html.lower()
