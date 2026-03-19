"""
TC-022: Escalation of Maintenance Requests
FR21: Categorize by priority, automatically escalating emergency requests.

Preconditions: There are maintenance requests of various priorities.
Steps: System organizes requests by priority.
Expected: Requests are listed in priority order (Urgent → High → Medium → Low).
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from models.maintenance_request import MaintenanceRequest
from conftest import login_as_admin
from datetime import date


def test_maintenance_sorted_by_priority(client, app, seed_users):
    """TC-022: Maintenance list shows requests sorted by priority (Urgent first)."""
    with app.app_context():
        mall = Mall(name='Escalate Mall', location='Escalate City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Esc-Unit', size=100,
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

        # Create requests with different priorities (insert in non-priority order)
        for priority, category in [
            ('Low', 'Cleaning'),
            ('Urgent', 'Structural'),
            ('Medium', 'Plumbing'),
            ('High', 'Electrical'),
        ]:
            mr = MaintenanceRequest(
                lease_id=lease.lease_id,
                category=category,
                description=f'{priority} priority issue',
                priority=priority, status='Open'
            )
            db.session.add(mr)
        db.session.commit()

        login_as_admin(client)

        response = client.get('/maintenance/')
        assert response.status_code == 200

        html = response.data.decode()

        # Verify priority order in the rendered HTML
        # Urgent should appear before High, High before Medium, Medium before Low
        urgent_pos = html.find('Urgent')
        high_pos = html.find('High')
        medium_pos = html.find('Medium')
        low_pos = html.find('Low')

        # All priorities should be present
        assert urgent_pos != -1
        assert high_pos != -1
        assert medium_pos != -1
        assert low_pos != -1

        # Urgent should come first, then High, then Medium, then Low
        assert urgent_pos < high_pos, 'Urgent should appear before High'
        assert high_pos < medium_pos, 'High should appear before Medium'
        assert medium_pos < low_pos, 'Medium should appear before Low'
