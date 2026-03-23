import pytest
import io
from unittest.mock import patch
from bs4 import BeautifulSoup
from datetime import date
from models import db
from models.rental_application import RentalApplication
from models.store_unit import StoreUnit

def test_list_applications_tenant(client, seed_users, seed_units):
    """Tenant only sees their own applications."""
    tenant_u = seed_users['tenant']
    u1, u2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        # Someone else's app
        other_app = RentalApplication(tenant_id=seed_users['admin'].user_id, unit_id=u2.unit_id, submission_date=date.today())
        # Tenant's app
        tenant_app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=u1.unit_id, submission_date=date.today())
        db.session.add_all([other_app, tenant_app])
        db.session.commit()
        other_id = other_app.application_id
        tenant_id = tenant_app.application_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/applications/')
    assert f'#appModal{tenant_id}'.encode() in resp.data
    assert f'#appModal{other_id}'.encode() not in resp.data

def test_list_applications_admin(client, seed_users, seed_units):
    """Admin sees all applications."""
    tenant_u = seed_users['tenant']
    u1, u2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        app1 = RentalApplication(tenant_id=seed_users['admin'].user_id, unit_id=u2.unit_id, submission_date=date.today())
        app2 = RentalApplication(tenant_id=tenant_u.user_id, unit_id=u1.unit_id, submission_date=date.today())
        db.session.add_all([app1, app2])
        db.session.commit()
        a1_id = app1.application_id
        a2_id = app2.application_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/applications/')
    assert f'#appModal{a1_id}'.encode() in resp.data
    assert f'#appModal{a2_id}'.encode() in resp.data

def test_submit_application_get(client, seed_users):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/applications/submit')
    assert resp.status_code == 200
    assert b'Submit Rental Application' in resp.data

def test_submit_application_post(client, seed_users, seed_units):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    unit = seed_units[0]
    
    data = {
        'unit_id': unit.unit_id,
        'documents': (io.BytesIO(b"dummy pdf content"), 'test.pdf')
    }
    resp = client.post('/applications/submit', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'Application submitted successfully.' in resp.data
    
    with client.application.app_context():
        app = RentalApplication.query.filter_by(tenant_id=seed_users['tenant'].user_id).first()
        assert app is not None
        assert app.unit_id == unit.unit_id
        assert len(app.documents) == 1
        assert app.documents[0].file_name == 'test.pdf'

def test_update_application_success(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    unit1, unit2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {
        'unit_id': unit2.unit_id,
        'documents': (io.BytesIO(b"dummy image content"), 'test.jpg')
    }
    resp = client.post(f'/applications/{app_id}/update', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'Application updated successfully.' in resp.data
    
    with client.application.app_context():
        updated = RentalApplication.query.get(app_id)
        assert updated.unit_id == unit2.unit_id
        assert len(updated.documents) == 1

def test_update_application_unauthorized(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    unit1 = seed_units[0]
    
    with client.application.app_context():
        app = RentalApplication(tenant_id=admin_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {'unit_id': unit1.unit_id}
    resp = client.post(f'/applications/{app_id}/update', data=data, follow_redirects=True)
    assert b'Unauthorized' in resp.data

def test_update_application_not_pending(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Approved')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {'unit_id': unit1.unit_id}
    resp = client.post(f'/applications/{app_id}/update', data=data, follow_redirects=True)
    assert b'Only pending applications can be updated' in resp.data

def test_approve_application(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/applications/{app_id}/approve', follow_redirects=True)
    assert b'Application approved' in resp.data
    
    with client.application.app_context():
        updated = RentalApplication.query.get(app_id)
        assert updated.status == 'Approved'

def test_reject_application(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/applications/{app_id}/reject', follow_redirects=True)
    assert b'Application rejected' in resp.data
    
    with client.application.app_context():
        updated = RentalApplication.query.get(app_id)
        assert updated.status == 'Rejected'


def test_submit_application_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during application submission."""
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post('/applications/submit', data={
            'unit_id': seed_units[0].unit_id,
        }, follow_redirects=True)
        assert b'An error occurred while submitting the application' in resp.data


def test_update_application_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during application update."""
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/applications/{app_id}/update', data={'unit_id': unit1.unit_id}, follow_redirects=True)
        assert b'An error occurred while updating the application' in resp.data


def test_approve_application_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during application approval."""
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/applications/{app_id}/approve', follow_redirects=True)
        assert b'An error occurred while approving the application' in resp.data


def test_reject_application_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during application rejection."""
    tenant_u = seed_users['tenant']
    unit1 = seed_units[0]
    with client.application.app_context():
        app = RentalApplication(tenant_id=tenant_u.user_id, unit_id=unit1.unit_id, submission_date=date.today(), status='Pending')
        db.session.add(app)
        db.session.commit()
        app_id = app.application_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/applications/{app_id}/reject', follow_redirects=True)
        assert b'An error occurred while rejecting the application' in resp.data
