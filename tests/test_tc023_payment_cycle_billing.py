"""
TC-023: Bill is Created Based on Payment Cycle
FR14: Allow tenants to choose a payment cycle and calculate rent dynamically.

Preconditions: A tenant has a lease.
Steps: Tenant chooses payment cycle. Bill is calculated per cycle.
Expected: Invoice reflects correct rent multiplier for the chosen cycle.
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from services.invoice_service import generate_invoice
from datetime import date


def test_monthly_invoice(app, seed_users):
    """TC-023a: Monthly lease invoice = 1× monthly rent."""
    _assert_invoice_for_cycle(app, 'Monthly', multiplier=1)


def test_quarterly_invoice(app, seed_users):
    """TC-023b: Quarterly lease invoice = 3× monthly rent."""
    _assert_invoice_for_cycle(app, 'Quarterly', multiplier=3)


def test_semi_annual_invoice(app, seed_users):
    """TC-023c: Semi-Annual lease invoice = 6× monthly rent."""
    _assert_invoice_for_cycle(app, 'Semi-Annual', multiplier=6)


def test_annual_invoice(app, seed_users):
    """TC-023d: Annual lease invoice = 12× monthly rent."""
    _assert_invoice_for_cycle(app, 'Annual', multiplier=12)


def _assert_invoice_for_cycle(app, cycle, multiplier):
    """Helper: verify that invoice total matches rent × cycle multiplier."""
    monthly_rate = Decimal('5000.00')
    expected_total = float(monthly_rate * multiplier)

    with app.app_context():
        mall = Mall(name=f'{cycle} Mall', location=f'{cycle} City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location=f'{cycle}-Unit', size=100,
            rental_rate=monthly_rate, availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()

        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle=cycle, status='Active'
        )
        db.session.add(lease)
        db.session.commit()

        invoice = generate_invoice(lease.lease_id, issue_date=date(2026, 3, 1))

        assert invoice is not None
        assert float(invoice.total_amount) == expected_total, (
            f'{cycle} invoice expected {expected_total}, got {float(invoice.total_amount)}'
        )
