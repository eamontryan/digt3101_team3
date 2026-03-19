"""
TC-005: Calculate Bill
FR19: Consolidate rent and utility charges into monthly bill.

Preconditions: Lease exists with monthly rent. Billing date reached.
Steps: System calculates rent, applies discounts if applicable, generates invoice.
Expected: Monthly bill is created with rent + utility charges included.
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from models.utility_usage import UtilityUsage
from models.invoice import Invoice
from services.invoice_service import generate_invoice
from datetime import date


def test_generate_invoice_with_utilities(app, seed_users):
    """TC-005: Invoice total must include rent + linked utility charges."""
    with app.app_context():
        mall = Mall(name='Bill Mall', location='500 Bill St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Bill-Unit', size=100,
            rental_rate=Decimal('5000.00'), availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()

        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle='Monthly', status='Active'
        )
        db.session.add(lease)
        db.session.commit()

        # Add un-invoiced utility usage
        u1 = UtilityUsage(
            unit_id=unit.unit_id, type='Electricity',
            usage_amount=Decimal('100.00'), billing_month=date(2026, 3, 1),
            amount=Decimal('800.00')
        )
        u2 = UtilityUsage(
            unit_id=unit.unit_id, type='Water',
            usage_amount=Decimal('30.00'), billing_month=date(2026, 3, 1),
            amount=Decimal('200.00')
        )
        db.session.add_all([u1, u2])
        db.session.commit()

        # Generate the invoice
        invoice = generate_invoice(lease.lease_id, issue_date=date(2026, 3, 1))

        assert invoice is not None
        # rent (5000) + electricity (800) + water (200) = 6000
        assert float(invoice.total_amount) == 6000.00

        # Verify utilities are linked to the invoice
        linked = UtilityUsage.query.filter_by(invoice_id=invoice.invoice_id).all()
        assert len(linked) == 2


def test_generate_invoice_rent_only(app, seed_users):
    """Invoice with no utilities should equal rent only."""
    with app.app_context():
        mall = Mall(name='Rent Mall', location='600 Rent St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Rent-Unit', size=100,
            rental_rate=Decimal('3000.00'), availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()
        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle='Monthly', status='Active'
        )
        db.session.add(lease)
        db.session.commit()

        invoice = generate_invoice(lease.lease_id, issue_date=date(2026, 3, 1))

        assert invoice is not None
        assert float(invoice.total_amount) == 3000.00
