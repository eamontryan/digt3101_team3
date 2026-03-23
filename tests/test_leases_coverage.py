import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup
from datetime import date, timedelta
from models import db
from models.lease import Lease
from models.store_unit import StoreUnit

def test_list_leases_tenant(client, seed_users, seed_units):
    """Test that a tenant only sees their own leases."""
    # Create two leases, one for tenant, one for someone else
    admin_user = seed_users['admin']
    tenant_user = seed_users['tenant']
    unit1, unit2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_user.user_id, unit_id=unit1.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        l2 = Lease(tenant_id=admin_user.user_id, unit_id=unit2.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        db.session.add_all([l1, l2])
        db.session.commit()
        l1_id = l1.lease_id
        l2_id = l2.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/leases/')
    assert resp.status_code == 200
    assert f'href="/leases/{l1_id}"'.encode() in resp.data
    assert f'href="/leases/{l2_id}"'.encode() not in resp.data

def test_list_leases_admin(client, seed_users, seed_units):
    """Test that an admin sees all leases."""
    admin_user = seed_users['admin']
    tenant_user = seed_users['tenant']
    unit1, unit2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_user.user_id, unit_id=unit1.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        l2 = Lease(tenant_id=admin_user.user_id, unit_id=unit2.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        db.session.add_all([l1, l2])
        db.session.commit()
        l1_id = l1.lease_id
        l2_id = l2.lease_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/leases/')
    assert resp.status_code == 200
    assert str(l1_id).encode() in resp.data
    assert str(l2_id).encode() in resp.data

def test_lease_detail(client, seed_users, seed_units):
    tenant_user = seed_users['tenant']
    unit1 = seed_units[0]
    
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_user.user_id, unit_id=unit1.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly', auto_renew=True, renewal_rate_increase=5.0)
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get(f'/leases/{l1_id}')
    assert resp.status_code == 200
    assert b'Monthly' in resp.data

def test_create_lease_get(client, seed_users, seed_units):
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/leases/create')
    assert resp.status_code == 200
    assert b'Create New Lease' in resp.data

def test_create_lease_post(client, seed_users, seed_units):
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    tenant = seed_users['tenant']
    unit = seed_units[0]
    
    resp = client.post('/leases/create', data={
        'tenant_id': tenant.user_id,
        'unit_id': unit.unit_id,
        'start_date': '2025-01-01',
        'end_date': '2025-12-31',
        'payment_cycle': 'Quarterly',
        'auto_renew': '1',
        'renewal_rate_increase': '2.5'
    }, follow_redirects=True)
    
    assert b'Lease created successfully.' in resp.data
    
    with client.application.app_context():
        lease = Lease.query.filter_by(tenant_id=tenant.user_id, unit_id=unit.unit_id).first()
        assert lease is not None
        assert lease.payment_cycle == 'Quarterly'
        assert lease.auto_renew is True
        assert lease.renewal_rate_increase == 2.5
        
        # Unit availability should be updated
        u = StoreUnit.query.get(unit.unit_id)
        assert u.availability == 'Occupied'

def test_sign_lease_get(client, seed_users, seed_units):
    tenant_user = seed_users['tenant']
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_user.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/leases/{l1_id}/sign')
    assert resp.status_code == 200
    assert b'Sign Lease Agreement' in resp.data

def test_sign_lease_post(client, seed_users, seed_units):
    tenant_user = seed_users['tenant']
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_user.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/leases/{l1_id}/sign', data={'signature': 'Tenant Signature'}, follow_redirects=True)
    assert b'Lease signed successfully.' in resp.data
    
    with client.application.app_context():
        l = Lease.query.get(l1_id)
        assert l.tenant_signature == 'Tenant Signature'

def test_terminate_lease_invalid_status(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly', status='Terminated')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/leases/{l1_id}/terminate', follow_redirects=True)
    assert b'Only active or pending leases can be terminated' in resp.data

def test_terminate_lease_success(client, seed_users, seed_units):
    unit = seed_units[0]
    with client.application.app_context():
        unit.availability = 'Occupied'
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=unit.unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/leases/{l1_id}/terminate', follow_redirects=True)
    assert b'Lease terminated successfully.' in resp.data
    
    with client.application.app_context():
        l = Lease.query.get(l1_id)
        assert l.status == 'Terminated'
        u = StoreUnit.query.get(unit.unit_id)
        assert u.availability == 'Available'

def test_download_agreement_unauthorized(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['admin'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today() + timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/leases/{l1_id}/download-agreement', follow_redirects=True)
    assert b'You are not authorized to download this agreement' in resp.data


def test_download_agreement_success(client, seed_users, seed_units):
    """Test successful PDF download covers generate_lease_pdf."""
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id,
                    start_date=date.today(), end_date=date.today() + timedelta(days=365),
                    payment_cycle='Monthly', status='Active',
                    tenant_signature='Tenant Sig', tenant_signed_at=date.today(),
                    agent_signature='Agent Sig', agent_signed_at=date.today(),
                    auto_renew=True, renewal_rate_increase=5.0)
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/leases/{l1_id}/download-agreement')
    assert resp.status_code == 200
    assert resp.content_type == 'application/pdf'


def test_create_lease_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during lease creation."""
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post('/leases/create', data={
            'tenant_id': seed_users['tenant'].user_id,
            'unit_id': seed_units[0].unit_id,
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'payment_cycle': 'Monthly',
            'renewal_rate_increase': ''
        }, follow_redirects=True)
        assert b'An error occurred while creating the lease' in resp.data


def test_terminate_lease_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during lease termination."""
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id,
                    start_date=date.today(), end_date=date.today() + timedelta(days=365),
                    payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/leases/{l1_id}/terminate', follow_redirects=True)
        assert b'An error occurred while terminating the lease' in resp.data
