import pytest
from unittest.mock import patch
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from models import db
from models.lease import Lease
from models.invoice import Invoice
from models.payment import Payment
from models.utility_usage import UtilityUsage
from models.maintenance_request import MaintenanceRequest
from models.notification import Notification
from services.invoice_service import generate_invoice, recalculate_invoice_total, check_overdue_invoices, generate_all_due_invoices

def test_generate_invoice_with_discount_and_utility(app, seed_users, seed_units):
    with app.app_context():
        tenant_u = seed_users['tenant']
        unit = seed_units[0]
        # Rent is 1000

        # Need 2 active leases to get the 5% multi-unit discount
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=unit.unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly', status='Active')
        l2 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[1].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly', status='Active')
        db.session.add_all([l1, l2])
        db.session.commit()
        l1_id = l1.lease_id

        # Add unbilled utility
        u1 = UtilityUsage(unit_id=unit.unit_id, type='Water', usage_amount=100.0, billing_month=date.today(), amount=50.0)
        db.session.add(u1)
        db.session.commit()
        
        # Add unbilled misuse charge
        m1 = MaintenanceRequest(lease_id=l1_id, category='Damage', status='Misuse', misuse_flag=True, charge_amount=75.0, priority='Low', description='Broken window')
        db.session.add(m1)
        db.session.commit()

        invoice = generate_invoice(l1_id)
        assert invoice is not None
        
        # Expected total = (1000 rent - 50 discount at 5%) + 50 utility + 75 misuse = 1075
        assert invoice.total_amount == 1075.0
        assert invoice.payments == []
        assert len(invoice.utility_usages) == 1
        assert len(invoice.maintenance_charges) == 1

def test_recalculate_invoice_total(app, seed_users, seed_units):
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id
        
        inv = Invoice(lease_id=l1_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000.0)
        db.session.add(inv)
        db.session.commit()
        inv_id = inv.invoice_id
        
        # Add utility linked to invoice
        u1 = UtilityUsage(unit_id=seed_units[0].unit_id, type='Water', usage_amount=100.0, billing_month=date.today(), amount=50.0, invoice_id=inv_id)
        db.session.add(u1)
        db.session.commit()
        
        # Recalculate
        invoice = Invoice.query.get(inv_id)
        recalculate_invoice_total(invoice)
        
        assert invoice.total_amount == 1050.0 # 1000 rent + 50 utility

def test_generate_all_due_invoices_missed_periods(app, seed_users, seed_units):
    with app.app_context():
        l1 = Lease(
            tenant_id=seed_users['tenant'].user_id,
            unit_id=seed_units[0].unit_id,
            start_date=date.today() - relativedelta(months=3), # 3 months ago
            end_date=date.today() + relativedelta(months=9),
            payment_cycle='Monthly',
            status='Active'
        )
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id
        
        # Call generate all
        generated = generate_all_due_invoices()
        
        # Should generate for 3 months ago, 2 months ago, 1 month ago, and today
        assert len(generated) == 4
        assert generated[-1].lease_id == l1_id
        
        # Generate again should yield 0
        generated_again = generate_all_due_invoices()
        assert len(generated_again) == 0

def test_generate_all_due_invoices_future_not_due(app, seed_users, seed_units):
    with app.app_context():
        l1 = Lease(
            tenant_id=seed_users['tenant'].user_id,
            unit_id=seed_units[0].unit_id,
            start_date=date.today(),
            end_date=date.today() + relativedelta(months=12),
            payment_cycle='Quarterly',
            status='Active'
        )
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id
        
        # Add one invoice for today
        inv = Invoice(lease_id=l1_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=3000.0)
        db.session.add(inv)
        db.session.commit()
        
        # Generate all should yield 0 since next quarterly bill isn't due for 3 months
        generated = generate_all_due_invoices()
        assert len(generated) == 0

def test_check_overdue_invoices(app, seed_users, seed_units):
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today()-timedelta(days=60), end_date=date.today()+timedelta(days=300), payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        
        # Invoice due yesterday
        i1 = Invoice(lease_id=l1.lease_id, issue_date=date.today()-timedelta(days=40), due_date=date.today()-timedelta(days=10), total_amount=1000, status='Pending')
        db.session.add(i1)
        db.session.commit()
        i1_id = i1.invoice_id

        # Make a partial payment
        p1 = Payment(invoice_id=i1_id, amount=200, status='Completed', due_date=date.today())
        db.session.add(p1)
        db.session.commit()

        check_overdue_invoices()
        
        invoice = Invoice.query.get(i1_id)
        assert invoice.status == 'Overdue'
        
        # Check notifications
        notifications = Notification.query.filter_by(related_entity='invoice').all()
        assert len(notifications) >= 2 # 1 for tenant, 1 for admin
        
        tenant_notif = Notification.query.filter_by(recipient_id=seed_users['tenant'].user_id, related_entity='invoice').first()
        assert tenant_notif is not None
        assert '800' in tenant_notif.message # 1000 - 200 partial payment = 800 balance


def test_generate_invoice_nonexistent_lease(app, seed_users):
    """Test generate_invoice returns None for nonexistent lease."""
    with app.app_context():
        result = generate_invoice(99999)
        assert result is None


def test_generate_invoice_with_explicit_dates(app, seed_users, seed_units):
    """Test generate_invoice with explicit issue_date and due_date."""
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id,
                    start_date=date.today(), end_date=date.today()+timedelta(days=365),
                    payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()

        issue = date.today() - timedelta(days=5)
        due = date.today() + timedelta(days=25)
        invoice = generate_invoice(l1.lease_id, issue_date=issue, due_date=due)
        assert invoice is not None
        assert invoice.issue_date == issue
        assert invoice.due_date == due


def test_generate_invoice_db_error(app, seed_users, seed_units):
    """Test rollback when db error occurs during invoice generation."""
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id,
                    start_date=date.today(), end_date=date.today()+timedelta(days=365),
                    payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            with pytest.raises(Exception):
                generate_invoice(l1_id)


def test_recalculate_invoice_db_error(app, seed_users, seed_units):
    """Test rollback when db error occurs during invoice recalculation."""
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id,
                    start_date=date.today(), end_date=date.today()+timedelta(days=365),
                    payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()

        inv = Invoice(lease_id=l1.lease_id, issue_date=date.today(), due_date=date.today()+timedelta(days=30), total_amount=1000)
        db.session.add(inv)
        db.session.commit()

        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            with pytest.raises(Exception):
                recalculate_invoice_total(inv)


def test_check_overdue_no_overdue(app, seed_users, seed_units):
    """Test check_overdue_invoices with no overdue invoices returns early."""
    with app.app_context():
        check_overdue_invoices()
        # No error, no notifications created
        assert Notification.query.count() == 0
