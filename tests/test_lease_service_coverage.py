import pytest
from decimal import Decimal
from datetime import date, timedelta
from models import db
from models.lease import Lease
from models.store_unit import StoreUnit
from models.notification import Notification
from services.lease_service import sign_lease, process_lease_renewals
from flask import session

def test_sign_lease_tenant(app, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    with app.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

        # We must simulate a request context with current_user
        with app.test_request_context():
            from flask_login import login_user
            login_user(tenant_u)
            
            lease = Lease.query.get(l1_id)
            sign_lease(lease, tenant_u, 'Tenant Sig')
            
            assert lease.tenant_signature == 'Tenant Sig'
            assert lease.tenant_signed_at is not None
            assert lease.signature_status == 'Partially Signed'
            
def test_sign_lease_agent(app, seed_users, seed_units):
    agent_u = seed_users['agent']
    with app.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

        with app.test_request_context():
            from flask_login import login_user
            login_user(agent_u)
            
            lease = Lease.query.get(l1_id)
            sign_lease(lease, agent_u, 'Agent Sig')
            
            assert lease.agent_signature == 'Agent Sig'
            assert lease.agent_signed_at is not None
            assert lease.signature_status == 'Partially Signed'

def test_sign_lease_fully_signed(app, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    admin_u = seed_users['admin']
    with app.app_context():
        l1 = Lease(tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, start_date=date.today(), end_date=date.today()+timedelta(days=365), payment_cycle='Monthly')
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id

        with app.test_request_context():
            from flask_login import login_user
            login_user(tenant_u)
            lease = Lease.query.get(l1_id)
            sign_lease(lease, tenant_u, 'Tenant Sig')

        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_u)
            # Admin role triggers LeasingAgent logic in lease_service because get_active_role returns Admin,
            # wait, sign_lease explicitly checks `elif role == 'LeasingAgent'`.
            # Admin actually would fail if not simulated as LeasingAgent unless get_active_role handles it.
            # In routes.__init__, Admin is returned for Dev, but Admin is Admin. 
            # Oh, if role == 'Admin', the current `sign_lease` function *does not* sign for agent! 
            # Let's mock a Dev user mapped to LeasingAgent, or just use agent.
            
            agent_u = seed_users['agent']
            login_user(agent_u)
            lease = Lease.query.get(l1_id)
            sign_lease(lease, agent_u, 'Agent Sig')
            
            assert lease.tenant_signature == 'Tenant Sig'
            assert lease.agent_signature == 'Agent Sig'
            assert lease.signature_status == 'Fully Signed'
            assert lease.status == 'Active'

def test_process_lease_renewals(app, seed_users, seed_units):
    with app.app_context():
        # Create a lease that ends in 10 days, has auto_renew, and 5% increase
        end = date.today() + timedelta(days=10)
        start = end - timedelta(days=365)
        
        unit = seed_units[0]
        original_rate = unit.rental_rate # 1000
        
        l1 = Lease(
            tenant_id=seed_users['tenant'].user_id,
            unit_id=unit.unit_id,
            start_date=start,
            end_date=end,
            payment_cycle='Monthly',
            status='Active',
            auto_renew=True,
            renewal_rate_increase=5.0,
            renewal_status='Not Applicable'
        )
        db.session.add(l1)
        db.session.commit()
        l1_id = l1.lease_id
        
        process_lease_renewals()
        
        l = Lease.query.get(l1_id)
        assert l.renewal_status == 'Renewed'
        assert l.start_date > end # New start date
        
        u = StoreUnit.query.get(unit.unit_id)
        assert u.rental_rate == original_rate * Decimal('1.05')
        
        notif = Notification.query.filter_by(recipient_id=seed_users['tenant'].user_id).first()
        assert notif is not None
        assert 'auto-renewed' in notif.message
