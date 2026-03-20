import pytest
from datetime import date, timedelta
from models import db
from models.store_unit import StoreUnit
from models.lease import Lease
from models.invoice import Invoice
from models.utility_usage import UtilityUsage

def test_list_utilities_admin(client, seed_users, seed_units):
    unit = seed_units[0]
    with client.application.app_context():
        u = UtilityUsage(unit_id=unit.unit_id, type='Electricity', usage_amount=100.0, billing_month=date.today(), amount=50.0)
        db.session.add(u)
        db.session.commit()

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/utilities/')
    assert resp.status_code == 200
    assert b'Electricity' in resp.data
    assert b'100.0' in resp.data

def test_add_utility_get(client, seed_users, seed_units):
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/utilities/add')
    assert resp.status_code == 200
    assert b'Record Utility Usage' in resp.data

def test_add_utility_post_linked_to_invoice(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    unit = seed_units[0]
    
    with client.application.app_context():
        unit.availability = 'Occupied'
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=unit.unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    
    data = {
        'unit_id': unit.unit_id,
        'invoice_id': i1_id,
        'type': 'Water',
        'usage_amount': '500.5',
        'billing_month': '2025-05-01',
        'amount': '25.0'
    }
    
    resp = client.post('/utilities/add', data=data, follow_redirects=True)
    assert b'Utility usage recorded' in resp.data
    
    with client.application.app_context():
        usage = UtilityUsage.query.filter_by(unit_id=unit.unit_id).first()
        assert usage is not None
        assert usage.type == 'Water'
        assert usage.amount == 25.0
        
        # The invoice total should have been recalculated (1000 + 25 = 1025)
        # However, recalculate_invoice_total re-applies rent based on unit.rental_rate.
        # So we just check that the invoice is updated.
        inv = Invoice.query.get(i1_id)
        assert inv.total_amount > 1000  # Will be 1000 rent + 25 utility

def test_add_utility_post_unlinked(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    unit = seed_units[0]
    
    with client.application.app_context():
        unit.availability = 'Occupied'
        db.session.commit()

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    
    data = {
        'unit_id': unit.unit_id,
        'invoice_id': '',  # Empty
        'type': 'Electricity',
        'usage_amount': '10.0',
        'billing_month': '2025-06-01',
        'amount': '15.0'
    }
    
    resp = client.post('/utilities/add', data=data, follow_redirects=True)
    assert b'Utility usage recorded' in resp.data
    
    with client.application.app_context():
        usage = UtilityUsage.query.filter_by(type='Electricity').first()
        assert usage is not None
        assert usage.invoice_id is None
