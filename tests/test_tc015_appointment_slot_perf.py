"""
TC-015: Schedule Viewing Appointment - Performance (Slot Lookup)
NFR1: UI actions should respond within 2 seconds.

Preconditions: Agent has availability; system contains 200+ appointments.
Steps: Go to Schedule Viewing, select unit, request available times. Measure.
Expected: Available slots display in ≤ 2.0 seconds.
"""
import time
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from models.appointment import Appointment
from models.user import User
from conftest import login_as_tenant
from datetime import datetime, timedelta


def test_schedule_page_response_time(client, app, seed_users):
    """TC-015: Schedule page with 200+ appointments loads in ≤ 2s."""
    with app.app_context():
        mall = Mall(name='Slot Mall', location='Slot City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Slot-Unit', size=100,
            rental_rate=5000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()

        agent = User.query.filter_by(role='LeasingAgent').first()
        tenant = User.query.filter_by(role='Tenant').first()

        # Seed 200+ appointments in the future
        base_time = datetime(2027, 1, 1, 9, 0)
        appointments = []
        for i in range(250):
            dt = base_time + timedelta(hours=i * 2)
            appointments.append(Appointment(
                agent_id=agent.user_id,
                tenant_id=tenant.user_id,
                unit_id=unit.unit_id,
                date_time=dt,
                end_time=dt + timedelta(hours=1),
                status='Scheduled'
            ))
        db.session.bulk_save_objects(appointments)
        db.session.commit()

        login_as_tenant(client)

        start = time.time()
        response = client.get('/appointments/schedule')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed <= 2.0, f'Schedule page took {elapsed:.2f}s, expected ≤ 2.0s'
