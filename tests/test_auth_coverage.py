import pytest
from bs4 import BeautifulSoup
from models import db
from models.user import User

def test_login_redirect_authenticated(client, seed_users):
    """Test accessing /login while already logged in redirects to dashboard."""
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/login', follow_redirects=True)
    assert b'Tenant Dashboard' in resp.data or b'Dashboard' in resp.data

def test_login_invalid_credentials(client, seed_users):
    """Test logging in with bad credentials shows an error."""
    resp = client.post('/login', data={'username': 'tenant_test', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b'Invalid username or password' in resp.data

def test_login_inactive_user(client, seed_users):
    """Test inactive users cannot log in."""
    with client.application.app_context():
        u = User.query.filter_by(username='tenant_test').first()
        u.status = 'Inactive'
        db.session.commit()
    
    resp = client.post('/login', data={'username': 'tenant_test', 'password': 'password123'}, follow_redirects=True)
    assert b'Your account is not active' in resp.data
    assert b'Tenant Dashboard' not in resp.data

def test_register_page_loads(client):
    resp = client.get('/register')
    assert resp.status_code == 200
    assert b'register' in resp.data.lower()

def test_register_redirect_authenticated(client, seed_users):
    """Test accessing /register while already logged in redirects to dashboard."""
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/register', follow_redirects=True)
    assert b'Tenant Dashboard' in resp.data or b'Dashboard' in resp.data

def test_register_success(client):
    """Test successful tenant registration."""
    resp = client.post('/register', data={
        'username': 'newtenant',
        'email': 'newtenant@test.com',
        'name': 'New Tenant',
        'phone': '555-0000',
        'password': 'securepass',
        'confirm_password': 'securepass'
    }, follow_redirects=True)
    
    assert b'Registration successful! Please log in.' in resp.data
    
    with client.application.app_context():
        u = User.query.filter_by(username='newtenant').first()
        assert u is not None
        assert u.role == 'Tenant'
        assert u.status == 'Active'

def test_register_password_mismatch(client):
    resp = client.post('/register', data={
        'username': 'badpass',
        'email': 'badpass@test.com',
        'name': 'Bad Pass',
        'password': 'pass',
        'confirm_password': 'notpass'
    }, follow_redirects=True)
    
    assert b'Passwords do not match' in resp.data

def test_register_duplicate_username(client, seed_users):
    resp = client.post('/register', data={
        'username': 'tenant_test', # Already exists
        'email': 'unique@test.com',
        'name': 'Dup User',
        'password': 'pass',
        'confirm_password': 'pass'
    }, follow_redirects=True)
    
    assert b'Username already taken' in resp.data

def test_register_duplicate_email(client, seed_users):
    resp = client.post('/register', data={
        'username': 'unique_user',
        'email': 'tenant@test.com', # Already exists
        'name': 'Dup Email',
        'password': 'pass',
        'confirm_password': 'pass'
    }, follow_redirects=True)
    
    assert b'Email already registered' in resp.data

def test_logout(client, seed_users):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/logout', follow_redirects=True)
    assert b'You have been logged out' in resp.data
    # Accessing authenticated page should now redirect to login
    resp2 = client.get('/', follow_redirects=True)
    assert b'name="username"' in resp2.data or b'Login' in resp2.data
