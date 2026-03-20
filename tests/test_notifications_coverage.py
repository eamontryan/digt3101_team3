import pytest
import json
from datetime import datetime
from models import db
from models.notification import Notification

def test_list_notifications(client, seed_users):
    tenant_u = seed_users['tenant']
    admin_u = seed_users['admin']

    with client.application.app_context():
        n1 = Notification(recipient_id=tenant_u.user_id, type='General', title='Test Title 1', message='Message 1')
        n2 = Notification(recipient_id=admin_u.user_id, type='General', title='Test Title 2', message='Message 2')
        db.session.add_all([n1, n2])
        db.session.commit()

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/notifications/')
    assert resp.status_code == 200
    assert b'Test Title 1' in resp.data
    assert b'Test Title 2' not in resp.data

def test_dismiss_notification_success(client, seed_users):
    tenant_u = seed_users['tenant']

    with client.application.app_context():
        n1 = Notification(recipient_id=tenant_u.user_id, type='General', title='Test Title 1', message='Message 1')
        db.session.add(n1)
        db.session.commit()
        n1_id = n1.notification_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/notifications/{n1_id}/dismiss', follow_redirects=True)
    assert b'Notification dismissed' in resp.data

    with client.application.app_context():
        n = Notification.query.get(n1_id)
        assert n is None

def test_dismiss_notification_unauthorized(client, seed_users):
    admin_u = seed_users['admin']

    with client.application.app_context():
        n1 = Notification(recipient_id=admin_u.user_id, type='General', title='Admin Notif', message='Message')
        db.session.add(n1)
        db.session.commit()
        n1_id = n1.notification_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/notifications/{n1_id}/dismiss', follow_redirects=True)
    assert b'Unauthorized' in resp.data

    with client.application.app_context():
        n = Notification.query.get(n1_id)
        assert n is not None

def test_api_notifications(client, seed_users):
    tenant_u = seed_users['tenant']

    with client.application.app_context():
        n1 = Notification(recipient_id=tenant_u.user_id, type='General', title='API Title', message='API Message')
        db.session.add(n1)
        db.session.commit()
        n1_id = n1.notification_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/notifications/api')
    assert resp.status_code == 200
    data = resp.json
    assert len(data) == 1
    assert data[0]['id'] == n1_id
    assert data[0]['title'] == 'API Title'
