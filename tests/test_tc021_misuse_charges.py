"""
TC-021: Apply Charges for Misused Maintenance Requests
FR22: Apply charges for misuse-related maintenance requests.

Preconditions: Tenant has submitted a maintenance request.
Steps: Admin marks it as misuse with charge → notification sent.
Expected: Misuse flag set, charge applied, tenant notified.
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from models.maintenance_request import MaintenanceRequest
from models.notification import Notification
from conftest import login_as_admin
from datetime import date


def test_mark_maintenance_as_misuse(client, app, seed_users):
    """TC-021: Admin can mark a maintenance request as misuse and charge the tenant."""
    with app.app_context():
        mall = Mall(name='Misuse Mall', location='Misuse City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Misuse-Unit', size=100,
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

        maint = MaintenanceRequest(
            lease_id=lease.lease_id,
            category='Cosmetic Damage',
            description='Tenant damaged storefront glass',
            priority='Medium', status='Open'
        )
        db.session.add(maint)
        db.session.commit()
        request_id = maint.request_id

        login_as_admin(client)

        response = client.post(f'/maintenance/{request_id}/update', data={
            'action': 'misuse',
            'charge_amount': '15000.00',
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify the request is marked as misuse
        updated = MaintenanceRequest.query.get(request_id)
        assert updated.misuse_flag is True
        assert updated.status == 'Misuse'
        assert float(updated.charge_amount) == 15000.00

        # Verify notification was created for the tenant
        notif = Notification.query.filter_by(
            recipient_id=tenant.user_id,
            type='Maintenance Update'
        ).first()
        assert notif is not None
        assert 'misuse' in notif.title.lower() or 'Misuse' in notif.message
