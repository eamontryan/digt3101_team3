"""
TC-007: Attempt to Sign Unapproved Lease Agreement
FR11: Allows user to electronically sign lease agreement.

Preconditions: Tenant has a Pending (unapproved) lease.
Steps: Click on an unapproved lease → attempt to sign it.
Expected: Signing proceeds but lease stays Partially Signed;
         lease does not become Active without agent co-signature.
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from services.lease_service import sign_lease
from datetime import date


def test_sign_pending_lease_stays_partial(app, seed_users):
    """TC-007: Tenant signing a Pending lease results in Partially Signed,
    not Active, because the agent hasn't co-signed."""
    with app.app_context():
        mall = Mall(name='Sign Mall', location='700 Sign St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Sign-Unit', size=100,
            rental_rate=Decimal('5000.00'), availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()

        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle='Monthly', status='Pending',
            signature_status='Unsigned'
        )
        db.session.add(lease)
        db.session.commit()

        # Tenant signs it
        with app.test_request_context():
            from flask_login import login_user
            login_user(tenant)
            sign_lease(lease, tenant, 'tenant_sig_token')

        # Lease should now be Partially Signed (not Fully Signed / Active)
        assert lease.signature_status == 'Partially Signed'
        assert lease.tenant_signature == 'tenant_sig_token'
        assert lease.agent_signature is None
        # Status should NOT be Active because agent hasn't co-signed
        assert lease.status != 'Active'


def test_fully_signed_lease_becomes_active(app, seed_users):
    """When both tenant and agent sign, the lease becomes Active and Fully Signed."""
    with app.app_context():
        mall = Mall(name='Full Mall', location='800 Full St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Full-Unit', size=100,
            rental_rate=Decimal('5000.00'), availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()
        agent = User.query.filter_by(username='agent_test').first()

        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle='Monthly', status='Pending',
            signature_status='Unsigned'
        )
        db.session.add(lease)
        db.session.commit()

        with app.test_request_context():
            from flask_login import login_user
            login_user(tenant)
            sign_lease(lease, tenant, 'tenant_sig')
        
        with app.test_request_context():
            from flask_login import login_user
            login_user(agent)
            sign_lease(lease, agent, 'agent_sig')

        assert lease.signature_status == 'Fully Signed'
        assert lease.status == 'Active'
