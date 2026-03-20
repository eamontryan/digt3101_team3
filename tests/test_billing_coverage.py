import pytest
from bs4 import BeautifulSoup
from datetime import date, timedelta
from models import db
from models.lease import Lease
from models.invoice import Invoice
from models.payment import Payment

def test_generate_invoices_admin(client, seed_users, seed_units):
    """Admin can trigger invoice generation."""
    with client.application.app_context():
        l1 = Lease(
            tenant_id=seed_users['tenant'].user_id,
            unit_id=seed_units[0].unit_id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            payment_cycle='Monthly',
            status='Active'
        )
        db.session.add(l1)
        db.session.commit()

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post('/billing/generate-invoices', follow_redirects=True)
    assert b'invoice(s) generated successfully' in resp.data

def test_generate_invoices_no_due(client, seed_users):
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post('/billing/generate-invoices', follow_redirects=True)
    assert b'No invoices are due at this time.' in resp.data

def test_list_invoices_tenant(client, seed_users, seed_units):
    """Tenant only sees their own invoices."""
    admin_u = seed_users['admin']
    tenant_u = seed_users['tenant']
    
    with client.application.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        l2 = Lease(tenant_id=admin_u.user_id, unit_id=seed_units[1].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add_all([l1, l2])
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        i2 = Invoice(lease_id=l2.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=2000)
        db.session.add_all([i1, i2])
        db.session.commit()
        i1_id = i1.invoice_id
        i2_id = i2.invoice_id
        
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/billing/invoices')
    assert b'1000' in resp.data
    assert b'2000' not in resp.data

def test_invoice_detail_json(client, seed_users, seed_units):
    """Test the JSON endpoint for invoice details."""
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get(f'/billing/invoices/{i1_id}/detail')
    assert resp.status_code == 200
    data = resp.json
    assert data['invoice_id'] == i1_id
    assert data['total_amount'] == 1000.0
    assert data['monthly_rate'] == 1000.0

def test_invoice_detail_unauthorized(client, seed_users, seed_units):
    """Tenant cannot view someone else's invoice."""
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['admin'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/billing/invoices/{i1_id}/detail')
    assert resp.status_code == 403
    assert b'Unauthorized' in resp.data

def test_pay_invoice_get(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get(f'/billing/invoices/{i1_id}/pay')
    assert resp.status_code == 200
    assert b'Pay' in resp.data

def test_pay_invoice_post_partial(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/billing/invoices/{i1_id}/pay', data={'amount': '500'}, follow_redirects=True)
    assert b'Payment recorded successfully' in resp.data
    
    with client.application.app_context():
        i = Invoice.query.get(i1_id)
        assert i.status in ('Paid', 'Partially Paid')
        assert len(i.payments) == 1
        assert i.payments[0].amount == 500

def test_pay_invoice_post_full(client, seed_users, seed_units):
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/billing/invoices/{i1_id}/pay', data={'amount': '1000'}, follow_redirects=True)
    
    with client.application.app_context():
        i = Invoice.query.get(i1_id)
        assert i.status == 'Paid'
