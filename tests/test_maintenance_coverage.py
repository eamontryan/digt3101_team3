import pytest
from datetime import date, timedelta
from models import db
from models.lease import Lease
from models.maintenance_request import MaintenanceRequest
from models.notification import Notification

def test_list_requests_tenant(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    admin_u = seed_users['admin']
    
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        m1 = MaintenanceRequest(lease_id=l1.lease_id, category='Plumbing', priority='Medium', status='Open')
        db.session.add(m1)
        db.session.commit()
        m1_id = m1.request_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/maintenance/')
    assert resp.status_code == 200
    assert b'Plumbing' in resp.data

def test_submit_request_get(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/maintenance/submit')
    assert resp.status_code == 200
    assert b'Submit Maintenance Request' in resp.data

def test_submit_request_post_urgent(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {
        'lease_id': l1_id,
        'category': 'Electrical',
        'description': 'Sparks flying',
        'priority': 'Urgent'
    }
    resp = client.post('/maintenance/submit', data=data, follow_redirects=True)
    assert b'Maintenance request submitted' in resp.data
    
    with client.application.app_context():
        req = MaintenanceRequest.query.filter_by(priority='Urgent').first()
        assert req is not None
        assert req.category == 'Electrical'
        
        # Verify notification was sent to admin
        admin = seed_users['admin']
        notif = Notification.query.filter_by(recipient_id=admin.user_id, related_entity='maintenance_request').first()
        assert notif is not None
        assert notif.title == 'Urgent Maintenance Request'

def test_request_detail_unauthorized(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    admin_u = seed_users['admin']
    
    with client.application.app_context():
        l1 = Lease(tenant_id=admin_u.user_id, unit_id=seed_units[1].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        m1 = MaintenanceRequest(lease_id=l1.lease_id, category='HVAC', priority='Low', status='Open')
        db.session.add(m1)
        db.session.commit()
        m1_id = m1.request_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/maintenance/{m1_id}', follow_redirects=True)
    assert b'You are not authorized to view this maintenance request.' in resp.data

def test_update_status_resolved(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        m1 = MaintenanceRequest(lease_id=l1.lease_id, category='Cleaning', priority='Low', status='Open')
        db.session.add(m1)
        db.session.commit()
        m1_id = m1.request_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/maintenance/{m1_id}/update', data={'action': 'update', 'status': 'Resolved'}, follow_redirects=True)
    assert b'Maintenance request updated' in resp.data
    
    with client.application.app_context():
        m = MaintenanceRequest.query.get(m1_id)
        assert m.status == 'Resolved'
        assert m.misuse_flag is False
        assert m.charge_amount is None

def test_update_status_misuse(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        m1 = MaintenanceRequest(lease_id=l1.lease_id, category='Wall Damage', priority='Low', status='Open')
        db.session.add(m1)
        db.session.commit()
        m1_id = m1.request_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/maintenance/{m1_id}/update', data={'action': 'misuse', 'charge_amount': '150.0'}, follow_redirects=True)
    assert b'Maintenance request updated' in resp.data
    
    with client.application.app_context():
        m = MaintenanceRequest.query.get(m1_id)
        assert m.status == 'Misuse'
        assert m.misuse_flag is True
        assert m.charge_amount == 150.0

def test_update_status_misuse_unauthorized(client, seed_users, seed_units):
    # Only Admin can mark Misuse, LeasingAgent cannot
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        m1 = MaintenanceRequest(lease_id=l1.lease_id, category='Glass', priority='Low', status='Open')
        db.session.add(m1)
        db.session.commit()
        m1_id = m1.request_id

    client.post('/login', data={'username': 'agent_test', 'password': 'password123'})
    resp = client.post(f'/maintenance/{m1_id}/update', data={'action': 'misuse', 'charge_amount': '150.0'}, follow_redirects=True)
    assert b'Only admins can mark a maintenance request as misuse' in resp.data
